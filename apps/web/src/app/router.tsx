import { createBrowserRouter } from 'react-router';
import { StatusPage } from '@/features/status/StatusPage';

export const router = createBrowserRouter([{ path: '/', element: <StatusPage /> }]);
