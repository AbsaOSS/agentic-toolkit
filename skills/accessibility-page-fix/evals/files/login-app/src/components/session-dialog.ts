import { createSignInForm } from './sign-in-form';

let open: HTMLElement | undefined;

/** "Please sign in again" dialog, shown over the current page when the session is about to expire. */
export function openSessionDialog(onSignedIn: () => void): void {
  if (open) return;
  const backdrop = document.createElement('div');
  backdrop.className = 'backdrop';
  const dialog = document.createElement('div');
  dialog.className = 'dialog';
  dialog.append(
    createSignInForm({
      title: 'Please sign in again',
      onSignedIn: () => {
        backdrop.remove();
        open = undefined;
        onSignedIn();
      },
    })
  );
  backdrop.append(dialog);
  document.body.append(backdrop);
  open = backdrop;
}
