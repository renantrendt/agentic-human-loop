'use client'

import Link from 'next/link'
import { FileText, Menu, X, ChevronLeft, ChevronRight } from 'lucide-react'
import { useState, useEffect, useRef } from 'react'
import { DocMetadata } from '@/lib/docs'

interface SidebarProps {
    sections: {
        name: string
        docs: DocMetadata[]
    }[]
    currentSection?: string
    currentSlug?: string
}

export function Sidebar({ sections, currentSection, currentSlug }: SidebarProps) {
    const [isOpen, setIsOpen] = useState(false)
    // Initialize from localStorage immediately to prevent flash
    const [isCollapsed, setIsCollapsed] = useState(() => {
        if (typeof window !== 'undefined') {
            const saved = localStorage.getItem('sidebar-collapsed')
            return saved === 'true'
        }
        return false
    })
    const activeItemRef = useRef<HTMLAnchorElement>(null)

    const sectionNames: Record<string, string> = {
        'developer-guide': 'Developer Guide',
        'user-guide': 'Writer Guide',
    }

    // Save collapsed state to localStorage when it changes
    useEffect(() => {
        if (typeof window !== 'undefined') {
            localStorage.setItem('sidebar-collapsed', String(isCollapsed))
        }
    }, [isCollapsed])

    // Auto-scroll to active item when page loads or changes
    useEffect(() => {
        if (activeItemRef.current && !isCollapsed) {
            activeItemRef.current.scrollIntoView({
                block: 'center',
                behavior: 'auto' // No animation, instant scroll
            })
        }
    }, [currentSection, currentSlug, isCollapsed])

    const sidebarContent = (
        <div className="h-full flex flex-col bg-secondary border-r border-border">
            <div className="p-6 border-b border-border flex items-center justify-between">
                <Link href="/" className="flex items-center gap-2 group">
                    {/* <div className="p-2 bg-primary/10 rounded-lg group-hover:bg-primary/20 transition-colors">
                        <FileText className="w-6 h-6 text-primary" />
                    </div> */}
                    <div>
                        <h1 className="text-xl font-bold text-foreground">Solidroad</h1>
                        <p className="text-xs text-muted-foreground">Athena E2E Docs</p>
                    </div>
                </Link>
                {/* Desktop collapse button */}
                <button
                    onClick={() => setIsCollapsed(!isCollapsed)}
                    className="hidden lg:block p-2 hover:bg-muted rounded-lg transition-colors"
                    aria-label={isCollapsed ? "Expand sidebar" : "Collapse sidebar"}
                >
                    {isCollapsed ? <Menu className="w-4 h-4" /> : <X className="w-4 h-4" />}
                </button>
            </div>

            <nav className="flex-1 overflow-y-auto p-4">
                {sections.map(({ name, docs }) => (
                    <div key={name} className="mb-6">
                        <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider mb-2 px-3">
                            {sectionNames[name] || name}
                        </h2>
                        <ul className="space-y-1">
                            {docs.map(doc => {
                                const isActive = currentSection === name && currentSlug === doc.slug
                                return (
                                    <li key={doc.slug}>
                                        <Link
                                            ref={isActive ? activeItemRef : null}
                                            href={`/${name}/${doc.slug}`}
                                            className={`
                        block px-3 py-2 rounded-lg text-sm transition-all
                        ${isActive
                                                    ? 'bg-primary text-primary-foreground font-medium shadow-lg shadow-primary/20'
                                                    : 'text-foreground hover:bg-muted hover:text-foreground'
                                                }
                      `}
                                            onClick={() => setIsOpen(false)}
                                        >
                                            {doc.title}
                                        </Link>
                                    </li>
                                )
                            })}
                        </ul>
                    </div>
                ))}
            </nav>

            {/* <div className="p-4 border-t border-border">
                <p className="text-xs text-muted-foreground text-center">
                    ATHENAHQ.AI
                </p>
            </div> */}
        </div>
    )

    return (
        <>
            {/* Mobile toggle button */}
            <button
                onClick={() => setIsOpen(!isOpen)}
                className="lg:hidden fixed top-4 left-4 z-50 p-2 bg-secondary border border-border rounded-lg shadow-lg hover:bg-muted transition-colors"
                aria-label="Toggle menu"
            >
                {isOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </button>

            {/* Desktop collapse/expand button */}
            {!isCollapsed && (
                <button
                    onClick={() => setIsCollapsed(true)}
                    className="hidden lg:block fixed top-4 left-[17rem] z-50 p-2 bg-secondary border border-border rounded-lg shadow-lg hover:bg-muted hover:border-primary transition-all"
                    aria-label="Collapse sidebar"
                    title="Collapse sidebar"
                >
                    <ChevronLeft className="w-4 h-4" />
                </button>
            )}
            {isCollapsed && (
                <button
                    onClick={() => setIsCollapsed(false)}
                    className="hidden lg:block fixed top-4 left-4 z-50 p-2 bg-secondary border border-border rounded-lg shadow-lg hover:bg-muted hover:border-primary transition-all"
                    aria-label="Expand sidebar"
                    title="Expand sidebar"
                >
                    <ChevronRight className="w-4 h-4" />
                </button>
            )}

            {/* Mobile overlay */}
            {isOpen && (
                <div
                    className="lg:hidden fixed inset-0 bg-black/50 z-30"
                    onClick={() => setIsOpen(false)}
                />
            )}

            {/* Sidebar */}
            <aside
                className={`
          fixed lg:sticky top-0 left-0 z-40 h-screen
          transform transition-all duration-300 ease-in-out
          ${isOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
          ${isCollapsed ? 'lg:w-0 lg:opacity-0' : 'w-72'}
        `}
            >
                {!isCollapsed && sidebarContent}
            </aside>
        </>
    )
}
