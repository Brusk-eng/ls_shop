const STORAGE_KEY = 'commera:welcome-seen'

export function hasSeenWelcome() {
  try {
    return localStorage.getItem(STORAGE_KEY) === '1'
  } catch {
    // Private mode. Seen-by-default is the safe failure: replaying a full-screen
    // greeting on every load is worse than never showing it.
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
