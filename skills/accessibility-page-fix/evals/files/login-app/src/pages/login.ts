import { createSignInForm } from '../components/sign-in-form';
import { navigate } from '../router';

export function renderLogin(root: HTMLElement): void {
  root.innerHTML = '<div class="login-page"><img class="logo" src="/logo.svg" /></div>';
  root.querySelector('.login-page')!.append(
    createSignInForm({ title: 'Sign in', onSignedIn: () => navigate('/account/settings') })
  );
}
