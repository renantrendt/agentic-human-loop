/** @type {import('tailwindcss').Config} */
module.exports = {
    content: [
        './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
        './src/components/**/*.{js,ts,jsx,tsx,mdx}',
        './src/app/**/*.{js,ts,jsx,tsx,mdx}',
    ],
    theme: {
        extend: {
            colors: {
                rose: {
                    50: '#fff1f2',
                    100: '#ffe4e6',
                    200: '#ffccd3',
                    300: '#ffa1ad',
                    400: '#ff637e',
                    500: '#ff2056',
                    600: '#ec003f',
                    700: '#c70036',
                    800: '#a50036',
                    900: '#8b0836',
                    950: '#4d0218',
                },
                background: 'var(--background)',
                foreground: 'var(--foreground)',
                primary: {
                    DEFAULT: 'var(--primary)',
                    foreground: 'var(--primary-foreground)',
                },
                secondary: {
                    DEFAULT: 'var(--secondary)',
                    foreground: 'var(--secondary-foreground)',
                },
                muted: {
                    DEFAULT: 'var(--muted)',
                    foreground: 'var(--muted-foreground)',
                },
                accent: {
                    DEFAULT: 'var(--accent)',
                    foreground: 'var(--accent-foreground)',
                },
                border: 'var(--border)',
                input: 'var(--input)',
                ring: 'var(--ring)',
            },
            typography: (theme) => ({
                DEFAULT: {
                    css: {
                        maxWidth: 'none',
                        color: theme('colors.foreground'),
                        a: {
                            color: theme('colors.primary.DEFAULT'),
                            '&:hover': {
                                color: theme('colors.primary.foreground'),
                            },
                        },
                        code: {
                            color: theme('colors.accent.foreground'),
                            backgroundColor: theme('colors.muted.DEFAULT'),
                            padding: '0.25rem 0.375rem',
                            borderRadius: '0.25rem',
                            fontWeight: '500',
                        },
                        'code::before': {
                            content: '""',
                        },
                        'code::after': {
                            content: '""',
                        },
                    },
                },
            }),
        },
    },
    plugins: [
        require('@tailwindcss/typography'),
    ],
}
