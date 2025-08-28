export interface Website {
  id: string;
  url: string;
  name: string;
  lastScan: string;
  complianceScore: number;
  status: 'active' | 'scanning' | 'analyzing' | 'error';
}