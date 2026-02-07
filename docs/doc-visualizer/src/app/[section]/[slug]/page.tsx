import { notFound } from 'next/navigation'
import { getDoc, getDocSections, getDocsForSection } from '@/lib/docs'
import { MarkdownViewer } from '@/components/MarkdownViewer'
import { Sidebar } from '@/components/Sidebar'
import { Calendar, Clock, ChevronLeft, ChevronRight } from 'lucide-react'
import Link from 'next/link'

interface PageProps {
    params: Promise<{
        section: string
        slug: string
    }>
}

export async function generateStaticParams() {
    const sections = getDocSections()
    const paths: { section: string; slug: string }[] = []

    sections.forEach(section => {
        const docs = getDocsForSection(section)
        docs.forEach(doc => {
            paths.push({
                section,
                slug: doc.slug,
            })
        })
    })

    return paths
}

export default async function DocPage({ params }: PageProps) {
    const { section, slug } = await params
    const doc = getDoc(section, slug)

    if (!doc) {
        notFound()
    }

    const sectionData = getDocSections().map(s => ({
        name: s,
        docs: getDocsForSection(s),
    }))

    // Get all docs in order for navigation
    const allDocs = sectionData.flatMap(s => 
        s.docs.map(d => ({ ...d, section: s.name }))
    )
    
    // Find current doc index
    const currentIndex = allDocs.findIndex(
        d => d.section === section && d.slug === slug
    )
    
    // Get previous and next docs
    const prevDoc = currentIndex > 0 ? allDocs[currentIndex - 1] : null
    const nextDoc = currentIndex < allDocs.length - 1 ? allDocs[currentIndex + 1] : null

    return (
        <div className="flex min-h-screen">
            <Sidebar sections={sectionData} currentSection={section} currentSlug={slug} />

            <main className="flex-1 overflow-y-auto relative">
                {/* Floating Navigation Arrows */}
                <div className="fixed top-6 right-6 z-30 flex items-center gap-2">
                    {prevDoc && (
                        <Link
                            href={`/${prevDoc.section}/${prevDoc.slug}`}
                            className="p-2 bg-secondary border border-border rounded-lg shadow-lg hover:bg-muted hover:border-primary transition-all"
                            title={`Previous: ${prevDoc.title}`}
                        >
                            <ChevronLeft className="w-5 h-5" />
                        </Link>
                    )}
                    {nextDoc && (
                        <Link
                            href={`/${nextDoc.section}/${nextDoc.slug}`}
                            className="p-2 bg-secondary border border-border rounded-lg shadow-lg hover:bg-muted hover:border-primary transition-all"
                            title={`Next: ${nextDoc.title}`}
                        >
                            <ChevronRight className="w-5 h-5" />
                        </Link>
                    )}
                </div>

                <article className="max-w-4xl mx-auto px-4 py-12 lg:px-8">
                    {/* Header */}
                    <header className="mb-8 pb-8 border-b border-border">
                        <div className="inline-block px-3 py-1 bg-primary/10 text-primary text-sm font-medium rounded-full mb-4">
                            {section === 'developer-guide' ? 'Developer Guide' : 'User Guide'}
                        </div>
                        <h1 className="text-4xl lg:text-5xl font-bold mb-4 bg-gradient-to-r from-foreground to-muted-foreground bg-clip-text text-transparent">
                            {doc.title}
                        </h1>
                        <div className="flex items-center gap-4 text-sm text-muted-foreground">
                            <div className="flex items-center gap-1.5">
                                <Calendar className="w-4 h-4" />
                                <span>Documentation</span>
                            </div>
                            <div className="flex items-center gap-1.5">
                                <Clock className="w-4 h-4" />
                                <span>{Math.ceil(doc.content.split(' ').length / 200)} min read</span>
                            </div>
                        </div>
                    </header>

                    {/* Content */}
                    <div className="mb-12">
                        <MarkdownViewer content={doc.content} />
                    </div>

                    {/* Footer */}
                    <footer className="pt-8 border-t border-border">
                        <p className="text-sm text-muted-foreground text-center">
                            Found an issue? Improve this documentation by editing the source file.
                        </p>
                    </footer>
                </article>
            </main>
        </div>
    )
}
