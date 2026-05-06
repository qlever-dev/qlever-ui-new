import type { Editor } from '../editor/init';
import type { TabState } from './types';
import { closeTab, createTab } from './operations';
import { state } from './state';
import { startRename } from './render';

export interface TabMenuItem {
  label: string;
  disabled?: boolean;
  onSelect: () => void;
}

let openMenu: HTMLElement | null = null;

export function showTabContextMenu(editor: Editor, tab: TabState, e: MouseEvent): void {
  e.preventDefault();
  closeMenu();

  const items: TabMenuItem[] = [
    {
      label: 'Duplicate',
      onSelect: () => douplicateTab(editor, tab),
    },
    {
      label: 'Rename',
      onSelect: () => requestRename(editor, tab),
    },
    {
      label: 'Close',
      disabled: state.tabs.length <= 1,
      onSelect: () => closeTab(editor, tab.id),
    },
  ];

  const menu = document.createElement('div');
  menu.className =
    'fixed z-50 min-w-[10rem] py-1 rounded-md border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 shadow-lg text-sm text-gray-700 dark:text-gray-200';
  menu.style.left = `${e.clientX}px`;
  menu.style.top = `${e.clientY}px`;

  for (const item of items) {
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.textContent = item.label;
    btn.disabled = !!item.disabled;
    btn.className = item.disabled
      ? 'block w-full text-left px-3 py-1.5 text-gray-400 dark:text-gray-500 cursor-not-allowed'
      : 'block w-full text-left px-3 py-1.5 hover:bg-gray-100 dark:hover:bg-gray-700';
    btn.addEventListener('click', () => {
      closeMenu();
      item.onSelect();
    });
    menu.appendChild(btn);
  }

  document.body.appendChild(menu);
  openMenu = menu;

  // Clamp to viewport.
  const rect = menu.getBoundingClientRect();
  if (rect.right > window.innerWidth) menu.style.left = `${window.innerWidth - rect.width - 4}px`;
  if (rect.bottom > window.innerHeight) menu.style.top = `${window.innerHeight - rect.height - 4}px`;

  // Defer dismissal listeners so the triggering right-click doesn't immediately close us.
  setTimeout(() => {
    document.addEventListener('mousedown', onDocumentMouseDown, true);
    document.addEventListener('keydown', onDocumentKeyDown, true);
    window.addEventListener('blur', closeMenu);
    window.addEventListener('resize', closeMenu);
  });
}

function closeMenu(): void {
  if (!openMenu) return;
  openMenu.remove();
  openMenu = null;
  document.removeEventListener('mousedown', onDocumentMouseDown, true);
  document.removeEventListener('keydown', onDocumentKeyDown, true);
  window.removeEventListener('blur', closeMenu);
  window.removeEventListener('resize', closeMenu);
}

function onDocumentMouseDown(e: MouseEvent): void {
  if (openMenu && !openMenu.contains(e.target as Node)) closeMenu();
}

function onDocumentKeyDown(e: KeyboardEvent): void {
  if (e.key === 'Escape') closeMenu();
}

function requestRename(editor: Editor, tab: TabState): void {
  const nameSpan = document.querySelector<HTMLElement>(`[data-tab-name="${tab.id}"]>span`) as HTMLSpanElement;
  console.log(nameSpan);

  startRename(editor, tab, nameSpan)
}

function douplicateTab(editor: Editor, tab: TabState) {
  console.log("duplicate", tab);
  createTab(editor, tab.name, tab.content);
}
