import type { Editor } from '../editor/init';

declare module '*?init' {
  const init: (...args: unknown[]) => Promise<unknown>;
  export default init;
}

declare global {
  interface Window {
    __editor?: Editor;
  }

  const __GIT_COMMIT__: string;
}
