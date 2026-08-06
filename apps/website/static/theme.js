(function () {
    const storageKey = 'theme'
    const darkTheme = 'dark'
    const lightTheme = 'light'
    const themeQuery = '(prefers-color-scheme: dark)'

    function storedTheme() {
        try {
            const value = localStorage.getItem(storageKey)
            return value === darkTheme || value === lightTheme ? value : null
        } catch (error) {
            return null
        }
    }

    function systemTheme() {
        return window.matchMedia && window.matchMedia(themeQuery).matches ? darkTheme : lightTheme
    }

    function currentTheme() {
        return storedTheme() || systemTheme()
    }

    function applyTheme(theme) {
        document.documentElement.dataset.theme = theme
        document.documentElement.style.colorScheme = theme

        const toggle = document.querySelector('[data-theme-toggle]')
        if (!toggle) return

        const darkActive = theme === darkTheme
        toggle.setAttribute('aria-pressed', String(darkActive))
        toggle.title = darkActive ? 'Switch to day mode' : 'Switch to night mode'

        const label = toggle.querySelector('[data-theme-toggle-label]')
        if (label) label.textContent = darkActive ? 'Day mode' : 'Night mode'
    }

    function saveTheme(theme) {
        try {
            localStorage.setItem(storageKey, theme)
        } catch (error) {
            return
        }
    }

    function toggleTheme() {
        const nextTheme = document.documentElement.dataset.theme === darkTheme ? lightTheme : darkTheme
        saveTheme(nextTheme)
        applyTheme(nextTheme)
    }

    document.addEventListener('DOMContentLoaded', function () {
        applyTheme(currentTheme())

        const toggle = document.querySelector('[data-theme-toggle]')
        if (toggle) {
            toggle.addEventListener('click', toggleTheme)
        }
    })

    if (window.matchMedia) {
        const mediaQuery = window.matchMedia(themeQuery)
        mediaQuery.addEventListener('change', function () {
            if (!storedTheme()) applyTheme(systemTheme())
        })
    }
})()
