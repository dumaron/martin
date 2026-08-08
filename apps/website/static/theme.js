(function () {
    const root = document.documentElement

    function applyTheme(theme) {
        root.dataset.theme = theme
        root.style.colorScheme = theme
    }

    function storedTheme() {
        try {
            const value = localStorage.getItem('theme')
            return value === 'dark' || value === 'light' ? value : null
        } catch (error) {
            return null
        }
    }

    document.addEventListener('click', function (event) {
        if (!event.target.closest('[data-theme-toggle]')) return

        const theme = root.dataset.theme === 'dark' ? 'light' : 'dark'
        try { localStorage.setItem('theme', theme) } catch (error) {}
        applyTheme(theme)
    })

    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', function (event) {
        if (!storedTheme()) applyTheme(event.matches ? 'dark' : 'light')
    })
})()
