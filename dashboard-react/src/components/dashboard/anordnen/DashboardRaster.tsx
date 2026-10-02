'use client';

/**
 * Anordenbare Dashboard-Startseite.
 *
 * Zwei Betriebsarten:
 *  - Ansicht: die Module werden genau wie bisher gerendert, ohne Hüllen,
 *    ohne Transformationen, ohne Drag-Kontext. Null Einfluss auf Overlays,
 *    Portale oder backdrop-filter der Module.
 *  - Anordnen: jedes Modul wird zu einer kompakten Kachel mit Griff,
 *    Pfeilen, Spaltenwechsel und Ausblenden. Ziehen per Maus, Finger oder
 *    Tastatur (dnd-kit); die Pfeilknöpfe sind der zweite, vollständige Weg.
 *
 * Das Layout selbst lebt in lib/dashboard-layout.ts (rein, getestet) und
 * wird vom Hook useDashboardLayout je Nutzer im Browser gespeichert.
 */

import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import {
  DndContext,
  DragOverlay,
  KeyboardSensor,
  MeasuringStrategy,
  PointerSensor,
  TouchSensor,
  closestCorners,
  useDroppable,
  useSensor,
  useSensors,
  type Announcements,
  type DragEndEvent,
  type DragOverEvent,
  type DragStartEvent,
  type ScreenReaderInstructions,
  type UniqueIdentifier,
} from '@dnd-kit/core';
import {
  SortableContext,
  sortableKeyboardCoordinates,
  useSortable,
  verticalListSortingStrategy,
} from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import {
  ArrowDown,
  ArrowLeftRight,
  ArrowUp,
  Check,
  EyeOff,
  GripVertical,
  LayoutGrid,
  Plus,
  RotateCcw,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { ErrorBoundary } from '@/components/ErrorBoundary';
import { spalteVon, type DashboardLayout, type Spalte } from '@/lib/dashboard-layout';
import { MODUL_JE_ID, type DashboardModul, type ModulKontext } from './modulkatalog';
import { useDashboardLayout } from './useDashboardLayout';

const SPALTEN_INFO: Record<Spalte, { titel: string; leer: string }> = {
  haupt: { titel: 'Hauptspalte', leer: 'Hauptspalte ist leer. Modul hierher ziehen.' },
  seite: { titel: 'Seitenspalte', leer: 'Seitenspalte ist leer. Modul hierher ziehen, oder leer lassen: dann nutzt die Hauptspalte die ganze Breite.' },
};

const ZONEN_ID: Record<Spalte, string> = { haupt: 'spalte:haupt', seite: 'spalte:seite' };

function modulName(id: UniqueIdentifier): string {
  return MODUL_JE_ID.get(String(id))?.titel ?? String(id);
}

function useReduzierteBewegung(): boolean {
  const [reduziert, setReduziert] = useState(false);
  useEffect(() => {
    const mq = window.matchMedia('(prefers-reduced-motion: reduce)');
    setReduziert(mq.matches);
    const h = (e: MediaQueryListEvent) => setReduziert(e.matches);
    mq.addEventListener('change', h);
    return () => mq.removeEventListener('change', h);
  }, []);
  return reduziert;
}

/* ------------------------------------------------------------------ */
/* Ansicht                                                             */
/* ------------------------------------------------------------------ */

interface DashboardRasterProps {
  userId: number | string | null | undefined;
  kontext: ModulKontext;
}

export const DashboardRaster: React.FC<DashboardRasterProps> = ({ userId, kontext }) => {
  const lay = useDashboardLayout(userId);
  const [anordnen, setAnordnen] = useState(false);
  const anordnenKnopf = useRef<HTMLButtonElement>(null);

  const beenden = useCallback(() => {
    setAnordnen(false);
    // Fokus zurück auf den Einstiegsknopf, sobald er wieder im Baum ist.
    requestAnimationFrame(() => anordnenKnopf.current?.focus());
  }, []);

  const verfuegbar = useCallback(
    (id: string) => {
      const m = MODUL_JE_ID.get(id);
      return !!m && (!m.verfuegbar || m.verfuegbar(kontext));
    },
    [kontext],
  );

  if (!lay.geladen) return null;

  if (anordnen) {
    return <AnordnenModus lay={lay} kontext={kontext} verfuegbar={verfuegbar} onFertig={beenden} />;
  }

  const haupt = lay.layout.haupt.filter(verfuegbar);
  const seite = lay.layout.seite.filter(verfuegbar);
  const seiteLeer = seite.length === 0;

  return (
    <>
      <div className="flex justify-end -mt-2 -mb-3">
        <button
          ref={anordnenKnopf}
          type="button"
          onClick={() => setAnordnen(true)}
          className="inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs font-medium text-gray-500 dark:text-zinc-500 hover:text-gray-900 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-zinc-800 transition-colors"
        >
          <LayoutGrid className="w-3.5 h-3.5" aria-hidden />
          Module anordnen
          {!lay.istStandard && (
            <span
              className="w-1.5 h-1.5 rounded-full bg-[#25bac8]"
              aria-label="eigene Anordnung aktiv"
              role="img"
            />
          )}
        </button>
      </div>

      <div className={cn('grid grid-cols-1 gap-5 items-start', !seiteLeer && 'xl:grid-cols-3')}>
        <div className={cn('flex flex-col gap-5 min-w-0', !seiteLeer && 'xl:col-span-2')}>
          {haupt.map((id) => (
            <ModulAnsicht key={id} id={id} kontext={kontext} />
          ))}
        </div>
        {!seiteLeer && (
          <div className="flex flex-col gap-5 min-w-0 xl:col-span-1">
            {seite.map((id) => (
              <ModulAnsicht key={id} id={id} kontext={kontext} />
            ))}
          </div>
        )}
      </div>
    </>
  );
};

const ModulAnsicht: React.FC<{ id: string; kontext: ModulKontext }> = ({ id, kontext }) => {
  const modul = MODUL_JE_ID.get(id);
  if (!modul) return null;
  return (
    <section aria-label={modul.titel} className="min-w-0">
      <ErrorBoundary componentName={modul.titel}>{modul.render(kontext)}</ErrorBoundary>
    </section>
  );
};

/* ------------------------------------------------------------------ */
/* Anordnen                                                            */
/* ------------------------------------------------------------------ */

type LayoutApi = ReturnType<typeof useDashboardLayout>;

interface AnordnenModusProps {
  lay: LayoutApi;
  kontext: ModulKontext;
  verfuegbar: (id: string) => boolean;
  onFertig: () => void;
}

const AnordnenModus: React.FC<AnordnenModusProps> = ({ lay, kontext, verfuegbar, onFertig }) => {
  const { layout } = lay;
  // Nur verfügbare Module sind sortierbar und sichtbar; die Positionen der
  // anderen bleiben im gespeicherten Layout unangetastet.
  const sichtbar = useMemo(
    () => ({ haupt: layout.haupt.filter(verfuegbar), seite: layout.seite.filter(verfuegbar) }),
    [layout, verfuegbar],
  );
  const layoutRef = useRef<DashboardLayout>(layout);
  layoutRef.current = layout;

  const [aktiv, setAktiv] = useState<string | null>(null);
  const [meldung, setMeldung] = useState('');
  const ueberschrift = useRef<HTMLHeadingElement>(null);
  const reduziert = useReduzierteBewegung();

  useEffect(() => {
    ueberschrift.current?.focus();
  }, []);

  // Escape beendet den Modus, außer dnd-kit braucht es gerade zum Abbrechen.
  useEffect(() => {
    const h = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && !aktiv) onFertig();
    };
    window.addEventListener('keydown', h);
    return () => window.removeEventListener('keydown', h);
  }, [aktiv, onFertig]);

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 6 } }),
    useSensor(TouchSensor, { activationConstraint: { delay: 180, tolerance: 8 } }),
    useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates }),
  );

  const spalteVonId = useCallback((id: UniqueIdentifier): Spalte | null => {
    const s = String(id);
    if (s === ZONEN_ID.haupt) return 'haupt';
    if (s === ZONEN_ID.seite) return 'seite';
    return spalteVon(layoutRef.current, s);
  }, []);

  const onDragStart = ({ active }: DragStartEvent) => setAktiv(String(active.id));

  // Spaltenwechsel passiert schon während des Ziehens, damit die Zielspalte
  // Platz macht und der Nutzer sieht, wo das Modul landen wird.
  const onDragOver = ({ active, over }: DragOverEvent) => {
    if (!over) return;
    const von = spalteVonId(active.id);
    const nach = spalteVonId(over.id);
    if (!von || !nach || von === nach) return;

    const zielListe = layoutRef.current[nach];
    const overIndex = zielListe.indexOf(String(over.id));
    let index = zielListe.length;
    if (overIndex >= 0) {
      const aktRect = active.rect.current.translated;
      const unterhalb = !!aktRect && over.rect && aktRect.top > over.rect.top + over.rect.height / 2;
      index = overIndex + (unterhalb ? 1 : 0);
    }
    lay.verschieben(String(active.id), nach, index);
  };

  const onDragEnd = ({ active, over }: DragEndEvent) => {
    setAktiv(null);
    if (!over) return;
    const von = spalteVonId(active.id);
    const nach = spalteVonId(over.id);
    if (!von || !nach || von !== nach) return;
    const liste = layoutRef.current[nach];
    const alt = liste.indexOf(String(active.id));
    const neu = liste.indexOf(String(over.id));
    if (neu >= 0 && alt !== neu) {
      lay.verschieben(String(active.id), nach, neu);
      setMeldung(`${modulName(active.id)} an Position ${neu + 1} in der ${SPALTEN_INFO[nach].titel}.`);
    }
  };

  const announcements: Announcements = useMemo(
    () => ({
      onDragStart: ({ active }) =>
        `${modulName(active.id)} aufgenommen. Pfeiltasten verschieben, Leertaste legt ab, Escape bricht ab.`,
      onDragOver: ({ active, over }) => {
        if (!over) return `${modulName(active.id)} ist über keinem Ablageplatz.`;
        const zone = spalteVonId(over.id);
        const istZone = String(over.id).startsWith('spalte:');
        return istZone
          ? `${modulName(active.id)} über der leeren ${zone ? SPALTEN_INFO[zone].titel : 'Spalte'}.`
          : `${modulName(active.id)} über ${modulName(over.id)}.`;
      },
      onDragEnd: ({ active, over }) =>
        over ? `${modulName(active.id)} abgelegt.` : `${modulName(active.id)} zurückgelegt.`,
      onDragCancel: ({ active }) => `Verschieben von ${modulName(active.id)} abgebrochen.`,
    }),
    [spalteVonId],
  );

  const srInstructions: ScreenReaderInstructions = {
    draggable:
      'Leertaste nimmt das Modul auf. Pfeiltasten verschieben es, Leertaste legt es ab, Escape bricht ab. Für den Spaltenwechsel gibt es einen eigenen Knopf.',
  };

  const handlung = (text: string, fn: () => void) => {
    fn();
    setMeldung(text);
  };

  const aktivesModul = aktiv ? MODUL_JE_ID.get(aktiv) : undefined;

  return (
    <DndContext
      sensors={sensors}
      collisionDetection={closestCorners}
      measuring={{ droppable: { strategy: MeasuringStrategy.Always } }}
      accessibility={{ announcements, screenReaderInstructions: srInstructions }}
      onDragStart={onDragStart}
      onDragOver={onDragOver}
      onDragEnd={onDragEnd}
      onDragCancel={() => setAktiv(null)}
    >
      <AnordnenLeiste
        lay={lay}
        verfuegbar={verfuegbar}
        ueberschriftRef={ueberschrift}
        onFertig={onFertig}
        onEinblenden={(id) => handlung(`${modulName(id)} wieder eingeblendet.`, () => lay.einblenden(id))}
        onZuruecksetzen={() => handlung('Standardanordnung wiederhergestellt.', lay.zuruecksetzen)}
      />

      <p role="status" aria-live="polite" className="sr-only">
        {meldung}
      </p>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-5 items-start">
        {(['haupt', 'seite'] as const).map((spalte) => (
          <SpaltenZone key={spalte} spalte={spalte} ids={sichtbar[spalte]}>
            {sichtbar[spalte].map((id, i) => {
              const modul = MODUL_JE_ID.get(id);
              if (!modul) return null;
              return (
                <ModulKachel
                  key={id}
                  modul={modul}
                  spalte={spalte}
                  position={i}
                  anzahl={sichtbar[spalte].length}
                  kontext={kontext}
                  reduziert={reduziert}
                  onSchritt={(r) =>
                    handlung(
                      `${modul.titel} nach ${r === 'auf' ? 'oben' : 'unten'} verschoben.`,
                      () => lay.schritt(id, r),
                    )
                  }
                  onSpalteWechseln={() =>
                    handlung(
                      `${modul.titel} in die ${spalte === 'haupt' ? 'Seitenspalte' : 'Hauptspalte'} verschoben.`,
                      () => lay.spalteWechseln(id),
                    )
                  }
                  onAusblenden={() =>
                    handlung(`${modul.titel} ausgeblendet. Oben in der Leiste wieder einblendbar.`, () =>
                      lay.ausblenden(id),
                    )
                  }
                />
              );
            })}
          </SpaltenZone>
        ))}
      </div>

      {typeof document !== 'undefined' &&
        createPortal(
          <DragOverlay dropAnimation={reduziert ? null : undefined}>
            {aktivesModul ? <SchwebeKarte modul={aktivesModul} /> : null}
          </DragOverlay>,
          document.body,
        )}
    </DndContext>
  );
};

/* ---------- Leiste ---------- */

interface AnordnenLeisteProps {
  lay: LayoutApi;
  verfuegbar: (id: string) => boolean;
  ueberschriftRef: React.RefObject<HTMLHeadingElement>;
  onFertig: () => void;
  onEinblenden: (id: string) => void;
  onZuruecksetzen: () => void;
}

const AnordnenLeiste: React.FC<AnordnenLeisteProps> = ({
  lay,
  verfuegbar,
  ueberschriftRef,
  onFertig,
  onEinblenden,
  onZuruecksetzen,
}) => {
  const ausgeblendet = lay.layout.ausgeblendet
    .filter(verfuegbar)
    .map((id) => MODUL_JE_ID.get(id))
    .filter((m): m is DashboardModul => !!m);

  return (
    <div
      role="region"
      aria-label="Anordnen-Werkzeuge"
      className="sticky top-2 z-30 rounded-2xl border border-[#25bac8]/40 bg-white/95 dark:bg-zinc-900/95 backdrop-blur-md shadow-lg shadow-black/5 dark:shadow-black/30"
    >
      <div className="px-4 sm:px-5 py-3 flex flex-col sm:flex-row sm:items-center gap-3">
        <div className="flex items-center gap-3 min-w-0 flex-1">
          <span
            className="shrink-0 w-9 h-9 rounded-xl flex items-center justify-center"
            style={{ background: 'var(--lime-dim)', color: 'var(--lime)' }}
            aria-hidden
          >
            <LayoutGrid className="w-[18px] h-[18px]" />
          </span>
          <div className="min-w-0">
            <h2
              ref={ueberschriftRef}
              tabIndex={-1}
              className="text-sm font-bold text-gray-900 dark:text-white outline-none"
            >
              Dashboard anordnen
            </h2>
            <p className="text-xs text-gray-500 dark:text-zinc-400 leading-snug">
              Module am Griff ziehen oder mit den Pfeilen verschieben. Tastatur: Leertaste greift,
              Pfeile bewegen, Leertaste legt ab. Jede Änderung wird sofort gespeichert.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 shrink-0">
          <button
            type="button"
            onClick={onZuruecksetzen}
            disabled={lay.istStandard}
            className="inline-flex items-center gap-1.5 px-3 py-2 rounded-xl text-sm font-medium border border-gray-300 dark:border-zinc-700 text-gray-700 dark:text-zinc-300 hover:bg-gray-50 dark:hover:bg-zinc-800 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          >
            <RotateCcw className="w-4 h-4" aria-hidden />
            Zurücksetzen
          </button>
          <button
            type="button"
            onClick={onFertig}
            className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl text-sm font-bold bg-[#25bac8] text-zinc-950 hover:bg-[#45d6e2] transition-colors"
          >
            <Check className="w-4 h-4" aria-hidden />
            Fertig
          </button>
        </div>
      </div>

      {ausgeblendet.length > 0 && (
        <div className="px-4 sm:px-5 py-2.5 border-t border-gray-200 dark:border-zinc-800 flex items-center gap-2 flex-wrap">
          <span className="text-[11px] font-semibold uppercase tracking-wider text-gray-500 dark:text-zinc-500 mr-1">
            Ausgeblendet
          </span>
          {ausgeblendet.map((m) => {
            const Icon = m.icon;
            return (
              <button
                key={m.id}
                type="button"
                onClick={() => onEinblenden(m.id)}
                className="inline-flex items-center gap-1.5 pl-2 pr-2.5 py-1 rounded-full text-xs font-medium border border-dashed border-gray-300 dark:border-zinc-700 text-gray-700 dark:text-zinc-300 hover:border-[#25bac8] hover:text-[#1597a3] dark:hover:text-[#25bac8] transition-colors"
                aria-label={`${m.titel} wieder einblenden`}
              >
                <Plus className="w-3 h-3" aria-hidden />
                <Icon className="w-3.5 h-3.5" aria-hidden />
                {m.titel}
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
};

/* ---------- Spalte ---------- */

interface SpaltenZoneProps {
  spalte: Spalte;
  ids: string[];
  children: React.ReactNode;
}

const SpaltenZone: React.FC<SpaltenZoneProps> = ({ spalte, ids, children }) => {
  const { setNodeRef, isOver, active } = useDroppable({ id: ZONEN_ID[spalte] });
  const leer = ids.length === 0;
  const info = SPALTEN_INFO[spalte];

  return (
    <div className={cn('min-w-0', spalte === 'haupt' ? 'xl:col-span-2' : 'xl:col-span-1')}>
      <div className="flex items-baseline justify-between px-1 mb-2">
        <span className="text-[11px] font-semibold uppercase tracking-wider text-gray-500 dark:text-zinc-500">
          {info.titel}
        </span>
        <span className="text-[11px] tabular-nums text-gray-400 dark:text-zinc-600">
          {ids.length} {ids.length === 1 ? 'Modul' : 'Module'}
        </span>
      </div>
      <SortableContext items={ids} strategy={verticalListSortingStrategy}>
        <div
          ref={setNodeRef}
          className={cn(
            'flex flex-col gap-3 rounded-2xl p-2 border-2 border-dashed transition-colors min-h-[7rem]',
            isOver
              ? 'border-[#25bac8] bg-[#25bac8]/5'
              : active
                ? 'border-gray-300 dark:border-zinc-700'
                : 'border-gray-200/80 dark:border-zinc-800',
          )}
        >
          {children}
          {leer && (
            <p className="m-auto px-4 py-6 text-center text-sm text-gray-500 dark:text-zinc-500 max-w-xs">
              {info.leer}
            </p>
          )}
        </div>
      </SortableContext>
    </div>
  );
};

/* ---------- Kachel ---------- */

interface ModulKachelProps {
  modul: DashboardModul;
  spalte: Spalte;
  position: number;
  anzahl: number;
  kontext: ModulKontext;
  reduziert: boolean;
  onSchritt: (richtung: 'auf' | 'ab') => void;
  onSpalteWechseln: () => void;
  onAusblenden: () => void;
}

const ModulKachel: React.FC<ModulKachelProps> = ({
  modul,
  spalte,
  position,
  anzahl,
  kontext,
  reduziert,
  onSchritt,
  onSpalteWechseln,
  onAusblenden,
}) => {
  const {
    attributes,
    listeners,
    setNodeRef,
    setActivatorNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: modul.id, transition: reduziert ? null : undefined });

  const Icon = modul.icon;
  const style: React.CSSProperties = {
    transform: CSS.Translate.toString(transform),
    transition,
  };

  return (
    <div
      ref={setNodeRef}
      style={style}
      className={cn(
        'rounded-2xl border bg-white dark:bg-zinc-900 border-gray-200 dark:border-zinc-800 overflow-hidden',
        isDragging && 'opacity-40 outline outline-2 outline-dashed outline-[#25bac8] outline-offset-2',
      )}
    >
      <div className="anordnen-kachel">
        {/* Bei schmaler Spalte rutscht die Knopfgruppe in eine zweite Zeile,
            statt den Titel abzuschneiden. */}
        <div className="flex flex-wrap items-center gap-x-2 gap-y-1 px-2.5 py-2 border-b border-gray-200 dark:border-zinc-800">
          <button
            ref={setActivatorNodeRef}
            type="button"
            {...attributes}
            {...listeners}
            aria-label={`${modul.titel} greifen und verschieben`}
            className="shrink-0 p-1.5 rounded-lg cursor-grab active:cursor-grabbing touch-none text-gray-400 dark:text-zinc-500 hover:text-gray-900 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-zinc-800"
          >
            <GripVertical className="w-4 h-4" aria-hidden />
          </button>
          <Icon className="w-4 h-4 shrink-0" style={{ color: 'var(--lime)' }} aria-hidden />
          <div className="min-w-[9rem] flex-1">
            <p className="text-sm font-semibold text-gray-900 dark:text-white truncate leading-tight">
              {modul.titel}
            </p>
            <p className="text-xs text-gray-500 dark:text-zinc-500 truncate">
              {modul.beschreibung}
            </p>
          </div>
          <div className="flex items-center gap-0.5 shrink-0 ml-auto" role="group" aria-label={`${modul.titel}: Position`}>
            <KachelKnopf
              label="nach oben"
              disabled={position === 0}
              onClick={() => onSchritt('auf')}
              icon={ArrowUp}
            />
            <KachelKnopf
              label="nach unten"
              disabled={position === anzahl - 1}
              onClick={() => onSchritt('ab')}
              icon={ArrowDown}
            />
            <KachelKnopf
              label={spalte === 'haupt' ? 'in die Seitenspalte' : 'in die Hauptspalte'}
              onClick={onSpalteWechseln}
              icon={ArrowLeftRight}
              className="hidden xl:inline-flex"
            />
            <KachelKnopf label="ausblenden" onClick={onAusblenden} icon={EyeOff} />
          </div>
        </div>

        {/* Verkleinerte, nicht bedienbare Vorschau: erkennbar, aber nicht im Weg. */}
        <div
          className="relative max-h-40 overflow-hidden pointer-events-none select-none"
          aria-hidden
          {...({ inert: '' } as Record<string, string>)}
        >
          <div className="p-2 opacity-80">
            <ErrorBoundary componentName={modul.titel}>{modul.render(kontext)}</ErrorBoundary>
          </div>
          <div className="absolute inset-x-0 bottom-0 h-14 bg-gradient-to-t from-white dark:from-zinc-900 to-transparent" />
        </div>
      </div>
    </div>
  );
};

interface KachelKnopfProps {
  label: string;
  icon: React.ElementType;
  onClick: () => void;
  disabled?: boolean;
  className?: string;
}

const KachelKnopf: React.FC<KachelKnopfProps> = ({ label, icon: Icon, onClick, disabled, className }) => (
  <button
    type="button"
    onClick={onClick}
    disabled={disabled}
    aria-label={label}
    title={label}
    className={cn(
      'inline-flex items-center justify-center w-8 h-8 rounded-lg text-gray-500 dark:text-zinc-400 hover:text-gray-900 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-zinc-800 disabled:opacity-30 disabled:cursor-not-allowed disabled:hover:bg-transparent transition-colors',
      className,
    )}
  >
    <Icon className="w-4 h-4" aria-hidden />
  </button>
);

/* ---------- Schwebende Karte beim Ziehen ---------- */

const SchwebeKarte: React.FC<{ modul: DashboardModul }> = ({ modul }) => {
  const Icon = modul.icon;
  return (
    <div className="w-72 max-w-[80vw] rounded-2xl border border-[#25bac8] bg-white dark:bg-zinc-900 shadow-2xl shadow-black/20 dark:shadow-black/60 px-4 py-3 flex items-center gap-3 -rotate-1 scale-[1.03] cursor-grabbing">
      <span
        className="shrink-0 w-9 h-9 rounded-xl flex items-center justify-center"
        style={{ background: 'var(--lime-dim)', color: 'var(--lime)' }}
      >
        <Icon className="w-[18px] h-[18px]" aria-hidden />
      </span>
      <div className="min-w-0">
        <p className="text-sm font-semibold text-gray-900 dark:text-white truncate">{modul.titel}</p>
        <p className="text-xs text-gray-500 dark:text-zinc-400">Loslassen, um abzulegen</p>
      </div>
    </div>
  );
};

