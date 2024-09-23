const copyToClipboard = async (textToCopy) => {
  // Navigator clipboard api needs a secure context (https)
  if (navigator.clipboard && window.isSecureContext) {
    await navigator.clipboard.writeText(textToCopy)
  } else {
    // Use the 'out of viewport hidden text area' trick
    const textArea = document.createElement("textarea")
    textArea.value = textToCopy

    // Move textarea out of the viewport so it's not visible
    textArea.style.position = "absolute"
    textArea.style.left = "-999999px"

    document.body.prepend(textArea)
    textArea.select()

    try {
      document.execCommand('copy')
    } catch (error) {
      // Do nothing
    } finally {
      textArea.remove()
    }
  }
}

const copyCurrentLink = async () => {
  try {
    const link = window.location.href
    await copyToClipboard(window.location.href)
    window.alert(`Link: ${link} copiado para a área de transferência`)
  } catch (e) {
    // Do nothing
  }
}
