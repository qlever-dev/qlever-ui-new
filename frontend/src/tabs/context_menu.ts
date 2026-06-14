import type { Editor } from '../editor/init';
import { closeTab, createTab, switchTab } from './operations';
import { startRename } from './render';
import { state } from './state';
import type { TabState } from './types';

export interface TabMenuItem {
  label: string;
  disabled?: boolean;
  onSelect: () => void;
}

let openMenu: HTMLElement | null = null;

export function showTabContextMenu(editor: Editor, tab: TabState, e: MouseEvent): void {
  e.preventDefault();
  closeMenu();

  const itemGroups: TabMenuItem[][] = [
    [
      {
        label: 'Duplicate',
        onSelect: () => douplicateTab(editor, tab),
      },
      {
        label: 'Rename',
        onSelect: () => requestRename(editor, tab),
      },
    ],
    [
      {
        label: 'Close',
        disabled: state.tabs.length <= 1,
        onSelect: () => closeTab(editor, tab.id),
      },
      {
        label: 'Close others',
        disabled: state.tabs.length <= 1,
        onSelect: () => closeOthers(editor, tab.id),
      },
      {
        label: 'Close tabs before',
        disabled: state.tabs[0].id === tab.id,
        onSelect: () => closeBefore(editor, tab),
      },
      {
        label: 'Close tabs after',
        disabled: state.tabs[state.tabs.length - 1].id === tab.id,
        onSelect: () => closeAfter(editor, tab),
      },
    ],
  ];

  const menu = document.createElement('div');
  menu.className =
    'fixed z-50 min-w-[10rem] py-2 rounded-md border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 shadow-lg text-sm text-gray-700 dark:text-gray-200';
  menu.style.left = `${e.clientX}px`;
  menu.style.top = `${e.clientY}px`;

  for (const [index, items] of itemGroups.entries()) {
    const groupContainer = document.createElement('div');
    groupContainer.className = 'px-2';
    for (const item of items) {
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.textContent = item.label;
      btn.disabled = !!item.disabled;
      btn.className = item.disabled
        ? 'block rounded w-full text-left px-3 py-1.5 text-gray-400 dark:text-gray-500 cursor-not-allowed'
        : 'block rounded w-full text-left px-3 py-1.5 hover:bg-gray-100 dark:hover:bg-gray-700';
      btn.addEventListener('click', () => {
        closeMenu();
        item.onSelect();
      });
      groupContainer.appendChild(btn);
    }
    menu.appendChild(groupContainer);
    if (index < itemGroups.length - 1) {
      const sep = document.createElement('div');
      sep.className = 'my-2 border-b border-gray-300 dark:border-gray-700';
      menu.appendChild(sep);
    }
  }

  document.body.appendChild(menu);
  openMenu = menu;

  // Clamp to viewport.
  const rect = menu.getBoundingClientRect();
  if (rect.right > window.innerWidth) menu.style.left = `${window.innerWidth - rect.width - 4}px`;
  if (rect.bottom > window.innerHeight)
    menu.style.top = `${window.innerHeight - rect.height - 4}px`;

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
  const nameSpan = document.querySelector<HTMLElement>(
    `[data-tab-name="${tab.id}"]>span`
  ) as HTMLSpanElement;
  startRename(editor, tab, nameSpan);
}

function douplicateTab(editor: Editor, tab: TabState) {
  createTab(editor, tab.name, tab.content);
}

async function closeAfter(editor: Editor, trigger_tab: TabState) {
  const trigger_tab_idx = state.tabs.findIndex((tab) => tab.id === trigger_tab.id);
  const active_tab_idx = state.tabs.findIndex((tab) => tab.id === state.activeTabId);
  if (active_tab_idx > trigger_tab_idx) {
    await switchTab(editor, trigger_tab.id);
  }
  const idsToClose = state.tabs.slice(trigger_tab_idx + 1).map((t) => t.id);
  for (const id of idsToClose) {
    await closeTab(editor, id);
  }
}

async function closeBefore(editor: Editor, trigger_tab: TabState) {
  const trigger_tab_idx = state.tabs.findIndex((tab) => tab.id === trigger_tab.id);
  const active_tab_idx = state.tabs.findIndex((tab) => tab.id === state.activeTabId);
  if (active_tab_idx < trigger_tab_idx) {
    await switchTab(editor, trigger_tab.id);
  }
  const idsToClose = state.tabs.slice(0, trigger_tab_idx).map((t) => t.id);
  for (const id of idsToClose) {
    await closeTab(editor, id);
  }
}

async function closeOthers(editor: Editor, id: string) {
  await switchTab(editor, id);
  const idsToClose = state.tabs.filter((t) => t.id !== id).map((t) => t.id);
  for (const closeId of idsToClose) {
    await closeTab(editor, closeId);
  }
}
