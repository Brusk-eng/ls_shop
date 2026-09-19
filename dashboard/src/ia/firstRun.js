// The greeting is a first-run moment, not a recurring one. It plays while the
// store is still being set up and never again once it has been seen.
const STORAGE_KEY = 'commera:welcome-seen'

export function hasSeenWelcome() {
  try {
    return localStorage.getItem(STORAGE_KEY) === '1'
  } catch {
    // Private mode. Treating it as already seen is the safe failure: replaying a
    // full-screen greeting on every load is far worse than never showing it.
    return true
  }
}

export function markWelcomeSeen() {
  try {
    localStorage.setItem(STORAGE_KEY, '1')
  } catch {
    /* private mode — the app still works, it just won't remember */
  }
}

export function forgetWelcomeSeen() {
  try {
    localStorage.removeItem(STORAGE_KEY)
  } catch {
    /* private mode */
  }
}
