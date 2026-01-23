/**
 * Cookie Compliance Management Page
 * Onboarding-Wizard: Scan → Services → Design → Integration
 */

import React, { useState, useEffect } from 'react';
import {
  Box,
  Container,
  Heading,
  Text,
  VStack,
  HStack,
  Button,
  Card,
  CardBody,
  Badge,
  Icon,
  useToast,
  Spinner,
  Input,
  Progress,
  Divider,
  SimpleGrid,
} from '@chakra-ui/react';
import {
  FiSearch,
  FiCheckCircle,
  FiSettings,
  FiCode,
  FiArrowRight,
  FiArrowLeft,
  FiCopy,
  FiCheck,
  FiRefreshCw,
} from 'react-icons/fi';
import { useRouter } from 'next/router';

// Components
import CookieBannerDesigner from './CookieBannerDesigner';
import ServiceManager from './ServiceManager';
import IntegrationGuide from './IntegrationGuide';

const STEPS = [
  { id: 1, title: 'Website scannen', icon: FiSearch, description: 'Cookies erkennen' },
  { id: 2, title: 'Services prüfen', icon: FiCheckCircle, description: 'Auswahl bestätigen' },
  { id: 3, title: 'Design anpassen', icon: FiSettings, description: 'Banner gestalten' },
  { id: 4, title: 'Integrieren', icon: FiCode, description: 'Code einbetten' },
];

const CookieCompliancePage: React.FC = () => {
  const router = useRouter();
  const toast = useToast();
  const [loading, setLoading] = useState(false);
  const [currentStep, setCurrentStep] = useState(1);
  const [siteId, setSiteId] = useState<string>('');
  const [config, setConfig] = useState<any>(null);
  
  // Step 1: Scan
  const [websiteUrl, setWebsiteUrl] = useState('');
  const [scanning, setScanning] = useState(false);
  const [scanResult, setScanResult] = useState<any>(null);
  
  // Step 2: Services
  const [selectedServices, setSelectedServices] = useState<string[]>([]);
  
  const API_URL = process.env.NEXT_PUBLIC_API_URL || 'https://api.complyo.tech';
  
  // Generate site ID from URL
  const generateSiteId = (url: string): string => {
    try {
      const urlObj = new URL(url.startsWith('http') ? url : `https://${url}`);
      const hostname = urlObj.hostname.replace('www.', '');
      return hostname.replace(/\./g, '-').toLowerCase();
    } catch {
      return 'unknown-site';
    }
  };
  
  // Step 1: Scan Website
  const handleScan = async () => {
    if (!websiteUrl) {
      toast({ title: 'Bitte URL eingeben', status: 'warning', duration: 3000 });
      return;
    }
    
    try {
      setScanning(true);
      setScanResult(null);
      
      const generatedSiteId = generateSiteId(websiteUrl);
      setSiteId(generatedSiteId);
      
      const response = await fetch(`${API_URL}/api/cookie-compliance/scan`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: websiteUrl, site_id: generatedSiteId }),
      });
      
      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          setScanResult(data);
          
          // Auto-select detected services
          if (data.detected_services?.length > 0) {
            setSelectedServices(data.detected_services.map((s: any) => s.service_key));
          }
          
          // Load config if exists
          const configResponse = await fetch(`${API_URL}/api/cookie-compliance/config/${generatedSiteId}`);
          if (configResponse.ok) {
            const configData = await configResponse.json();
            if (configData.success) {
              setConfig(configData.data);
            }
          }
          
          toast({ title: 'Scan abgeschlossen!', status: 'success', duration: 3000 });
        }
      }
    } catch (error) {
      console.error('Scan error:', error);
      toast({ title: 'Scan fehlgeschlagen', status: 'error', duration: 3000 });
    } finally {
      setScanning(false);
    }
  };
  
  // Save config
  const saveConfig = async (newConfig: any) => {
    try {
      const response = await fetch(`${API_URL}/api/cookie-compliance/config`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ ...newConfig, site_id: siteId }),
      });
      
      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          setConfig(newConfig);
          return true;
        }
      }
      return false;
    } catch {
      return false;
    }
  };
  
  // Next Step
  const nextStep = async () => {
    if (currentStep === 2) {
      // Save services when leaving step 2
      await saveConfig({ ...config, services: selectedServices });
    }
    if (currentStep < 4) {
      setCurrentStep(currentStep + 1);
    }
  };
  
  // Previous Step
  const prevStep = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1);
    }
  };
  
  // Can proceed to next step?
  const canProceed = () => {
    switch (currentStep) {
      case 1: return scanResult !== null;
      case 2: return true; // Can always proceed from services (even with 0)
      case 3: return true; // Can always proceed from design
      default: return false;
    }
  };
  
  // Render Step Content
  const renderStepContent = () => {
    switch (currentStep) {
      case 1:
        return (
          <VStack spacing={6} align="stretch">
            <Box textAlign="center" py={4}>
              <Icon as={FiSearch} boxSize={12} color="orange.400" mb={4} />
              <Heading size="md" mb={2}>Website scannen</Heading>
              <Text color="gray.500">
                Geben Sie Ihre Website-URL ein, um automatisch alle Cookies zu erkennen.
              </Text>
            </Box>
            
            <HStack>
              <Input
                placeholder="https://ihre-website.de"
                value={websiteUrl}
                onChange={(e) => setWebsiteUrl(e.target.value)}
                size="lg"
                bg="gray.800"
                border="1px solid"
                borderColor="gray.600"
                _focus={{ borderColor: 'orange.400' }}
              />
              <Button
                colorScheme="orange"
                size="lg"
                onClick={handleScan}
                isLoading={scanning}
                loadingText="Scannt..."
                leftIcon={<FiSearch />}
                minW="150px"
              >
                Scannen
              </Button>
            </HStack>
            
            {scanning && (
              <Box py={4}>
                <Progress size="sm" isIndeterminate colorScheme="orange" borderRadius="full" />
                <Text fontSize="sm" color="gray.400" mt={2} textAlign="center">
                  Analysiere {websiteUrl}...
                </Text>
              </Box>
            )}
            
            {scanResult && (
              <Card bg={scanResult.total_found > 0 ? 'green.900' : 'blue.900'} borderColor={scanResult.total_found > 0 ? 'green.500' : 'blue.500'} borderWidth={1}>
                <CardBody>
                  <VStack align="start" spacing={3}>
                    <HStack>
                      <Icon as={FiCheckCircle} color={scanResult.total_found > 0 ? 'green.400' : 'blue.400'} boxSize={6} />
                      <Text fontWeight="bold" fontSize="lg">
                        {scanResult.total_found > 0 
                          ? `${scanResult.total_found} Service(s) erkannt`
                          : 'Keine Tracking-Cookies gefunden'}
                      </Text>
                    </HStack>
                    
                    {scanResult.detected_services?.length > 0 ? (
                      <HStack flexWrap="wrap" gap={2}>
                        {scanResult.detected_services.map((s: any) => (
                          <Badge key={s.service_key} colorScheme="green" fontSize="sm" px={2} py={1}>
                            {s.name}
                          </Badge>
                        ))}
                      </HStack>
                    ) : (
                      <Text fontSize="sm" color="gray.400">
                        Ihre Website benötigt möglicherweise keinen Cookie-Banner. 
                        Sie können im nächsten Schritt trotzdem Services manuell hinzufügen.
                      </Text>
                    )}
                  </VStack>
                </CardBody>
              </Card>
            )}
          </VStack>
        );
        
      case 2:
        return (
          <VStack spacing={6} align="stretch">
            <Box textAlign="center" py={4}>
              <Icon as={FiCheckCircle} boxSize={12} color="orange.400" mb={4} />
              <Heading size="md" mb={2}>Services bestätigen</Heading>
              <Text color="gray.500">
                Überprüfen Sie die erkannten Services und fügen Sie ggf. weitere hinzu.
              </Text>
            </Box>
            
            <ServiceManager
              selectedServices={selectedServices}
              onServicesChange={setSelectedServices}
            />
          </VStack>
        );
        
      case 3:
        return (
          <VStack spacing={6} align="stretch">
            <Box textAlign="center" py={4}>
              <Icon as={FiSettings} boxSize={12} color="orange.400" mb={4} />
              <Heading size="md" mb={2}>Banner gestalten</Heading>
              <Text color="gray.500">
                Passen Sie das Aussehen Ihres Cookie-Banners an.
              </Text>
            </Box>
            
            <CookieBannerDesigner
              config={config}
              siteId={siteId}
              onSave={saveConfig}
            />
          </VStack>
        );
        
      case 4:
        return (
          <VStack spacing={6} align="stretch">
            <Box textAlign="center" py={4}>
              <Icon as={FiCode} boxSize={12} color="green.400" mb={4} />
              <Heading size="md" mb={2}>🎉 Fast geschafft!</Heading>
              <Text color="gray.500">
                Kopieren Sie den Code und fügen Sie ihn in Ihre Website ein.
              </Text>
            </Box>
            
            {selectedServices.length === 0 ? (
              <Card bg="blue.900" borderColor="blue.500" borderWidth={1}>
                <CardBody textAlign="center" py={8}>
                  <Icon as={FiCheckCircle} boxSize={10} color="blue.400" mb={4} />
                  <Heading size="md" mb={2}>Kein Banner erforderlich</Heading>
                  <Text color="gray.400">
                    Ihre Website verwendet keine Tracking-Cookies, die eine Einwilligung erfordern.
                    Sie müssen keinen Cookie-Banner einbinden.
                  </Text>
                </CardBody>
              </Card>
            ) : (
              <IntegrationGuide siteId={siteId} config={config} />
            )}
          </VStack>
        );
        
      default:
        return null;
    }
  };
  
  return (
    <Container maxW="container.lg" py={8}>
      <VStack spacing={8} align="stretch">
        {/* Header */}
        <Box textAlign="center">
          <Heading size="xl" mb={2}>🍪 Cookie-Compliance Setup</Heading>
          <Text color="gray.400">
            In 4 einfachen Schritten zum DSGVO-konformen Cookie-Banner
          </Text>
        </Box>
        
        {/* Progress Steps */}
        <Box>
          <HStack justify="center" spacing={0} mb={4}>
            {STEPS.map((step, index) => (
              <React.Fragment key={step.id}>
                <VStack 
                  spacing={1} 
                  cursor={step.id <= currentStep ? 'pointer' : 'default'}
                  onClick={() => step.id <= currentStep && setCurrentStep(step.id)}
                  opacity={step.id <= currentStep ? 1 : 0.4}
                  transition="all 0.2s"
                >
                  <Box
                    w={12}
                    h={12}
                    borderRadius="full"
                    bg={step.id < currentStep ? 'green.500' : step.id === currentStep ? 'orange.500' : 'gray.600'}
                    display="flex"
                    alignItems="center"
                    justifyContent="center"
                    transition="all 0.2s"
                  >
                    {step.id < currentStep ? (
                      <Icon as={FiCheck} color="white" boxSize={6} />
                    ) : (
                      <Icon as={step.icon} color="white" boxSize={5} />
                    )}
                  </Box>
                  <Text fontSize="xs" fontWeight={step.id === currentStep ? 'bold' : 'normal'} color={step.id === currentStep ? 'orange.400' : 'gray.400'}>
                    {step.title}
                  </Text>
                </VStack>
                
                {index < STEPS.length - 1 && (
                  <Box 
                    h="2px" 
                    w="80px" 
                    bg={step.id < currentStep ? 'green.500' : 'gray.600'} 
                    mx={2}
                    mt={-4}
                  />
                )}
              </React.Fragment>
            ))}
          </HStack>
          
          <Progress 
            value={(currentStep / STEPS.length) * 100} 
            colorScheme="orange" 
            size="sm" 
            borderRadius="full"
            bg="gray.700"
          />
        </Box>
        
        {/* Step Content */}
        <Card bg="gray.800" borderColor="gray.700" borderWidth={1}>
          <CardBody p={8}>
            {renderStepContent()}
          </CardBody>
        </Card>
        
        {/* Navigation */}
        <HStack justify="space-between">
          <Button
            variant="ghost"
            leftIcon={<FiArrowLeft />}
            onClick={prevStep}
            isDisabled={currentStep === 1}
          >
            Zurück
          </Button>
          
          {currentStep < 4 ? (
            <Button
              colorScheme="orange"
              rightIcon={<FiArrowRight />}
              onClick={nextStep}
              isDisabled={!canProceed()}
              size="lg"
            >
              Weiter
            </Button>
          ) : (
            <Button
              colorScheme="green"
              leftIcon={<FiCheckCircle />}
              onClick={() => router.push('/dashboard')}
              size="lg"
            >
              Fertig
            </Button>
          )}
        </HStack>
      </VStack>
    </Container>
  );
};

export default CookieCompliancePage;
