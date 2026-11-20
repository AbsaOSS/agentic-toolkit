import { signIn, SignInError } from '../auth';
import { notify } from './notifications';

/**
 * The sign-in form. Used as the whole login page and, when the session is about to expire, inside the
 * "Please sign in again" dialog on top of any other page.
 */
export function createSignInForm(options: { title: string; onSignedIn: () => void }): HTMLElement {
  const form = document.createElement('form');
  form.className = 'sign-in';
  form.noValidate = true;
  form.innerHTML = `
    <div class="sign-in__title"></div>
    <input class="sign-in__field" name="username" type="text" placeholder="Username" autocomplete="off" />
    <input class="sign-in__field" name="password" type="password" placeholder="Password" autocomplete="off" />
    <div class="sign-in__error" hidden></div>
    <button class="sign-in__submit" type="submit">Sign in</button>
  `;
  form.querySelector('.sign-in__title')!.textContent = options.title;
  const error = form.querySelector<HTMLElement>('.sign-in__error')!;
  form.addEventListener('submit', async event => {
    event.preventDefault();
    const data = new FormData(form);
    const username = String(data.get('username') ?? '').trim();
    const password = String(data.get('password') ?? '');
    if (!username || !password) {
      error.textContent = 'Enter your username and password.';
      error.hidden = false;
      return;
    }
    error.hidden = true;
    try {
      await signIn(username, password);
      options.onSignedIn();
    } catch (failure) {
      notify(failure instanceof SignInError ? failure.message : 'Sign-in failed. Try again later.');
    }
  });
  return form;
}
