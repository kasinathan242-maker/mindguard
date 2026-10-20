import { createBrowserRouter } from 'react-router';
import { AppLayout } from '@/app/AppLayout';
import { HomePage } from '@/features/home/HomePage';
import { AgeGatePage } from '@/features/onboarding/AgeGatePage';
import { ConsentPage } from '@/features/onboarding/ConsentPage';
import { LandingPage } from '@/features/onboarding/LandingPage';
import { LoginPage } from '@/features/onboarding/LoginPage';
import { Under18Page } from '@/features/onboarding/Under18Page';
import { PrivacyPage } from '@/features/privacy/PrivacyPage';
import { StatusPage } from '@/features/status/StatusPage';

export const routes = [
  { path: '/', element: <LandingPage /> },
  { path: '/start', element: <AgeGatePage /> },
  { path: '/start/under-18', element: <Under18Page /> },
  { path: '/start/consent', element: <ConsentPage /> },
  { path: '/login', element: <LoginPage /> },
  { path: '/status', element: <StatusPage /> },
  {
    path: '/app',
    element: <AppLayout />,
    children: [
      { index: true, element: <HomePage /> },
      { path: 'privacy', element: <PrivacyPage /> },
    ],
  },
];

export const router = createBrowserRouter(routes);
