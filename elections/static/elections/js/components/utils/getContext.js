export const getContext = () => {
  const context = {}
  // Extracting context from HTML scripts application/json
  document.querySelectorAll("script[type='application/json']").forEach(el => {
    context[`${el.id}`] = JSON.parse(document.getElementById(el.id).textContent)
  })
  return context 
}

