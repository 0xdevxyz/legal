/**
 * Cookie Compliance Management Page
 * Main dashboard for cookie consent management
 */

import React, { useState, useEffect } from 'react';
import {
  Box,
  Container,
  Heading,
  Text,
  Tabs,
  TabList,
  TabPanels,
  Tab,
  TabPanel,
  VStack,
  HStack,
  Button,
  Card,
  CardBody,
  Badge,
  Icon,
  useToast,
  Alert,
  AlertIcon,
  Spinner,
  Grid,
  GridItem,
} from '@chakra-ui/react';
import {
  FiSettings,
  FiEye,
  FiCode,
  FiBarChart2,
  FiCheckCircle,
  FiAlertCircle,
  FiCopy,
} from 'react-icons/fi';
import { useRouter } from 'next/router';

// Components
import CookieBannerDesigner from './CookieBannerDesigner';
import ServiceManager from './ServiceManager';
import IntegrationGuide from './IntegrationGuide';
import ConsentStatistics from './ConsentStatistics';

interface CookieCompliancePageProps {}

const CookieCompliancePage: React.FC<CookieCompliancePageProps> = () => {
  const router = useRouter();
  const toast = useToast();
  const [loading, setLoading] = useState(true);
  const [siteId, setSiteId] = useState<string>('');
  const [config, setConfig] = useState<any>(null);
  const [activeTab, setActiveTab] = useState(0);
  
  useEffect(() => {
    loadConfig();
  }, []);
  
  const loadConfig = async () => {
    try {
      setLoading(true);
      
      const API_URL = process.env.NEXT_PUBLIC_API_URL || 'https://api.complyo.tech';
      
      // ✅ Erst Website-Info laden
      const websiteResponse = await fetch(`${API_URL}/api/v2/websites`, {
        credentials: 'include',
      });
      
      if (!websiteResponse.ok || !websiteResponse) {
        console.log('Keine Websites konfiguriert');
        setLoading(false);
        return;
      }
      
      const websiteData = await websiteResponse.json();
      if (!websiteData.success || !websiteData.websites?.length) {
        console.log('Keine Websites verfügbar');
        setLoading(false);
        return;
      }
      
      // ✅ Site-ID aus echter Website generieren
      const primaryWebsite = websiteData.websites.find((w: any) => w.is_primary) || websiteData.websites[0];
      const generatedSiteId = generateSiteIdFromUrl(primaryWebsite.url);
      setSiteId(generatedSiteId);
      
      // ✅ Jetzt Config mit echter Site-ID laden
      const response = await fetch(`${API_URL}/api/cookie-compliance/config/${generatedSiteId}`, {
        credentials: 'include',
      });
      
      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          setConfig(data.data);
        }
      }
    } catch (error) {
      console.error('Error loading config:', error);
      toast({
        title: 'Fehler beim Laden',
        description: 'Konfiguration konnte nicht geladen werden.',
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
    } finally {
      setLoading(false);
    }
  };
  
  const generateSiteIdFromUrl = (url: string): string => {
    try {
      const urlObj = new URL(url.startsWith('http') ? url : `https://${url}`);
      const hostname = urlObj.hostname.replace('www.', '');
      return hostname.replace(/\./g, '-').toLowerCase();
    } catch {
      return 'unknown-site';
    }
  };
  
  const saveConfig = async (newConfig: any) => {
    try {
      const API_URL = process.env.NEXT_PUBLIC_API_URL || 'https://api.complyo.tech';
      const response = await fetch(`${API_URL}/api/cookie-compliance/config`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({
          ...newConfig,
          site_id: siteId,
        }),
      });
      
      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          setConfig(newConfig);
          toast({
            title: 'Gespeichert',
            description: 'Cookie-Banner-Konfiguration wurde gespeichert.',
            status: 'success',
            duration: 3000,
            isClosable: true,
          });
          return true;
        }
      }
      
      throw new Error('Save failed');
    } catch (error) {
      console.error('Error saving config:', error);
      toast({
        title: 'Fehler beim Speichern',
        description: 'Konfiguration konnte nicht gespeichert werden.',
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
      return false;
    }
  };
  
  if (loading) {
    return (
      <Container maxW="container.xl" py={8}>
        <VStack spacing={4} align="center" justify="center" minH="400px">
          <Spinner size="xl" color="blue.500" />
          <Text>Lade Cookie-Compliance-Konfiguration...</Text>
        </VStack>
      </Container>
    );
  }
  
  return (
    <Container maxW="container.xl" py={8}>
      <VStack spacing={8} align="stretch">
        {/* Header */}
        <Box>
          <HStack justify="space-between" mb={4}>
            <VStack align="start" spacing={1}>
              <Heading size="lg">🍪 Cookie-Compliance</Heading>
              <Text color="gray.600">
                DSGVO-konformes Cookie-Management für Ihre Website
              </Text>
            </VStack>
            
            <HStack>
              <Badge colorScheme="green" fontSize="md" px={3} py={1}>
                <HStack spacing={2}>
                  <Icon as={FiCheckCircle} />
                  <span>Aktiv</span>
                </HStack>
              </Badge>
            </HStack>
          </HStack>
          
          {/* Quick Stats */}
          <Grid templateColumns="repeat(4, 1fr)" gap={4} mb={6}>
            <GridItem>
              <Card>
                <CardBody>
                  <VStack align="start" spacing={1}>
                    <Text fontSize="sm" color="gray.600">Opt-In-Rate</Text>
                    <Heading size="lg" color="green.500">--</Heading>
                    <Text fontSize="xs" color="gray.500">Letzte 30 Tage</Text>
                  </VStack>
                </CardBody>
              </Card>
            </GridItem>
            
            <GridItem>
              <Card>
                <CardBody>
                  <VStack align="start" spacing={1}>
                    <Text fontSize="sm" color="gray.600">Consents</Text>
                    <Heading size="lg">--</Heading>
                    <Text fontSize="xs" color="gray.500">Gesamt</Text>
                  </VStack>
                </CardBody>
              </Card>
            </GridItem>
            
            <GridItem>
              <Card>
                <CardBody>
                  <VStack align="start" spacing={1}>
                    <Text fontSize="sm" color="gray.600">Services</Text>
                    <Heading size="lg">{config?.services?.length || 0}</Heading>
                    <Text fontSize="xs" color="gray.500">Aktiv</Text>
                  </VStack>
                </CardBody>
              </Card>
            </GridItem>
            
            <GridItem>
              <Card>
                <CardBody>
                  <VStack align="start" spacing={1}>
                    <Text fontSize="sm" color="gray.600">Banner</Text>
                    <Badge colorScheme="blue" fontSize="md">
                      {config?.layout || 'banner_bottom'}
                    </Badge>
                    <Text fontSize="xs" color="gray.500">Layout</Text>
                  </VStack>
                </CardBody>
              </Card>
            </GridItem>
          </Grid>
        </Box>
        
        {/* Setup Alert */}
        {(!config?.services || config.services.length === 0) && (
          <Alert status="warning" borderRadius="md">
            <AlertIcon />
            <Box flex="1">
              <Text fontWeight="bold">Setup erforderlich</Text>
              <Text fontSize="sm">
                Konfigurieren Sie Ihr Cookie-Banner und wählen Sie die Services aus, die Sie verwenden.
              </Text>
            </Box>
            <Button
              size="sm"
              colorScheme="orange"
              onClick={() => setActiveTab(1)}
            >
              Jetzt einrichten
            </Button>
          </Alert>
        )}
        
        {/* Main Content - Tabs */}
        <Card>
          <CardBody>
            <Tabs
              index={activeTab}
              onChange={setActiveTab}
              variant="soft-rounded"
              colorScheme="blue"
            >
              <TabList mb={6}>
                <Tab>
                  <HStack spacing={2}>
                    <Icon as={FiSettings} />
                    <span>Design</span>
                  </HStack>
                </Tab>
                <Tab>
                  <HStack spacing={2}>
                    <Icon as={FiEye} />
                    <span>Services</span>
                  </HStack>
                </Tab>
                <Tab>
                  <HStack spacing={2}>
                    <Icon as={FiCode} />
                    <span>Integration</span>
                  </HStack>
                </Tab>
                <Tab>
                  <HStack spacing={2}>
                    <Icon as={FiBarChart2} />
                    <span>Statistiken</span>
                  </HStack>
                </Tab>
              </TabList>
              
              <TabPanels>
                {/* Design Tab */}
                <TabPanel>
                  <CookieBannerDesigner
                    config={config}
                    siteId={siteId}
                    onSave={saveConfig}
                  />
                </TabPanel>
                
                {/* Services Tab */}
                <TabPanel>
                  <ServiceManager
                    selectedServices={config?.services || []}
                    onServicesChange={(services) => {
                      saveConfig({ ...config, services });
                    }}
                  />
                </TabPanel>
                
                {/* Integration Tab */}
                <TabPanel>
                  <IntegrationGuide siteId={siteId} config={config} />
                </TabPanel>
                
                {/* Statistics Tab */}
                <TabPanel>
                  <ConsentStatistics siteId={siteId} />
                </TabPanel>
              </TabPanels>
            </Tabs>
          </CardBody>
        </Card>
      </VStack>
    </Container>
  );
};

export default CookieCompliancePage;

