import { MetadataRoute } from 'next';

export default function sitemap(): MetadataRoute.Sitemap {
  const baseUrl = 'https://complyo.de';

  // Hinweis: next.config.js setzt trailingSlash: true — die URLs hier muessen
  // deshalb mit Slash enden, sonst faengt sich jeder Crawler einen 308-Hop ein.
  return [
    { url: `${baseUrl}/`, lastModified: new Date(), changeFrequency: 'weekly', priority: 1 },

    // Tool-Landingpages
    { url: `${baseUrl}/dsgvo-website-check/`, lastModified: new Date(), changeFrequency: 'weekly', priority: 0.9 },
    { url: `${baseUrl}/bfsg-check/`, lastModified: new Date(), changeFrequency: 'weekly', priority: 0.9 },
    { url: `${baseUrl}/barrierefreiheit-website-testen/`, lastModified: new Date(), changeFrequency: 'weekly', priority: 0.9 },

    // Ratgeber
    { url: `${baseUrl}/ratgeber/`, lastModified: new Date(), changeFrequency: 'weekly', priority: 0.7 },
    { url: `${baseUrl}/ratgeber/barrierefreiheit-website-checkliste/`, lastModified: new Date(), changeFrequency: 'monthly', priority: 0.8 },
    { url: `${baseUrl}/ratgeber/cookie-banner-pflicht/`, lastModified: new Date(), changeFrequency: 'monthly', priority: 0.8 },
    { url: `${baseUrl}/ratgeber/wordpress-cookie-banner/`, lastModified: new Date(), changeFrequency: 'monthly', priority: 0.8 },

    // Rechtstexte
    { url: `${baseUrl}/impressum/`, lastModified: new Date(), changeFrequency: 'monthly', priority: 0.5 },
    { url: `${baseUrl}/datenschutz/`, lastModified: new Date(), changeFrequency: 'monthly', priority: 0.5 },
    { url: `${baseUrl}/agb/`, lastModified: new Date(), changeFrequency: 'monthly', priority: 0.5 },
    { url: `${baseUrl}/gdpr/`, lastModified: new Date(), changeFrequency: 'monthly', priority: 0.4 },
  ];
}
