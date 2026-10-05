import { toast } from 'frappe-ui'

// The clipboard is refused outright over plain http and in some embedded
// browsers, so the link is put in front of the merchant to copy by hand.
export async function copyLink(url) {
  try {
    await navigator.clipboard.writeText(url)
    toast.success('Link copied')
  } catch {
    toast.error('Could not copy the link', { description: url })
  }
}
