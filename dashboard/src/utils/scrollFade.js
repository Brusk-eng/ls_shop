// Sub-pixel layout keeps scrollTop/scrollLeft a fraction short of their maximum, so an
// exact comparison would leave the end fade painted forever.
const SLACK = 1

const trackers = new WeakMap()

// A frappe-ui ScrollArea (SettingsBody included) scrolls its viewport, not its root; the
// mask still goes on the root so the fade stays pinned while the viewport moves under it.
function scrollerOf(element) {
  if (element.matches('[data-slot="scroll-area"]')) {
    return element.querySelector(':scope > [data-slot="scroll-area-viewport"]') ?? element
  }
  return element
}

function updateEdges(element, scroller) {
  const maxScrollLeft = scroller.scrollWidth - scroller.clientWidth
  // RTL counts scrollLeft down from 0 into the negatives, so 0 is the right edge there.
  const isRightToLeft = getComputedStyle(scroller).direction === 'rtl'
  const distanceFromLeft = isRightToLeft ? maxScrollLeft + scroller.scrollLeft : scroller.scrollLeft
  const distanceFromBottom = scroller.scrollHeight - scroller.clientHeight - scroller.scrollTop

  element.classList.toggle('scroll-fade-top', scroller.scrollTop > SLACK)
  element.classList.toggle('scroll-fade-bottom', distanceFromBottom > SLACK)
  element.classList.toggle('scroll-fade-left', distanceFromLeft > SLACK)
  element.classList.toggle('scroll-fade-right', maxScrollLeft - distanceFromLeft > SLACK)
}

export const scrollFade = {
  mounted(element) {
    const scroller = scrollerOf(element)
    const update = () => updateEdges(element, scroller)

    // The scroller resizing changes what overflows; a child resizing means the content
    // itself changed (rows loaded, a section expanded). New children are observed as they land.
    const resizeObserver = new ResizeObserver(update)
    resizeObserver.observe(scroller)
    for (const child of scroller.children) resizeObserver.observe(child)
    const mutationObserver = new MutationObserver((mutations) => {
      for (const mutation of mutations) {
        for (const node of mutation.addedNodes) {
          if (node instanceof Element) resizeObserver.observe(node)
        }
      }
      update()
    })
    mutationObserver.observe(scroller, { childList: true })

    scroller.addEventListener('scroll', update, { passive: true })
    element.classList.add('scroll-fade')
    trackers.set(element, { scroller, update, resizeObserver, mutationObserver })
    update()
  },
  unmounted(element) {
    const tracker = trackers.get(element)
    if (!tracker) return
    tracker.scroller.removeEventListener('scroll', tracker.update)
    tracker.resizeObserver.disconnect()
    tracker.mutationObserver.disconnect()
    trackers.delete(element)
  },
}
