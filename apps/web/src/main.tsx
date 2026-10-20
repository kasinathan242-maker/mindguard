import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { RouterProvider } from 'react-router/dom';
import { Providers } from '@/app/providers';
import { router } from '@/app/router';
import '@/lib/i18n';
import './index.css';

const root = document.getElementById('root');
if (!root) throw new Error('Root element #root is missing from index.html');

createRoot(root).render(
  <StrictMode>
    <Providers>
      <RouterProvider router={router} />
    </Providers>
  </StrictMode>,
);
