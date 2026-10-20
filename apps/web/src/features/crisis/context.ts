import { createContext, useContext } from 'react';

export interface CrisisContextValue {
  openCrisis: () => void;
}

export const CrisisContext = createContext<CrisisContextValue | null>(null);

export function useCrisis(): CrisisContextValue {
  const context = useContext(CrisisContext);
  if (!context) throw new Error('useCrisis must be used inside <CrisisProvider>');
  return context;
}
