const header = document.querySelector('.candidacy-name')

const observer = new IntersectionObserver((entries) => {
  const secondaryHeader = document.querySelector('.candidacy-name-secondary')
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      secondaryHeader.classList.add('visually-hidden')
    } else {
      secondaryHeader.classList.remove('visually-hidden')
    }
  })
})

observer.observe(header)
