document.addEventListener('DOMContentLoaded', function() {
  const tabLinks = document.querySelectorAll('.tab-link')

  tabLinks.forEach(function(tabLink) {
    tabLink.addEventListener('click', function() {
      // Rimuovi la classe active da tutti i tab
      tabLinks.forEach(link => link.classList.remove('active'))

      // Nascondi tutti i contenuti
      document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active')
      })

      // Attiva il tab corrente
      this.classList.add('active')

      // Mostra il contenuto corrispondente
      const tabId = this.getAttribute('data-tab')
      document.getElementById(tabId).classList.add('active')
    })
  })
})