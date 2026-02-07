import Link from 'next/link'
import { ArrowRight, BookOpen, Code } from 'lucide-react'
import { getDocSections, getDocsForSection } from '@/lib/docs'
import { Sidebar } from '@/components/Sidebar'

export default function HomePage() {
    const sectionData = getDocSections().map(section => ({
        name: section,
        docs: getDocsForSection(section),
    }))

    const totalDocs = sectionData.reduce((sum, s) => sum + s.docs.length, 0)

    return (
        <div className="flex min-h-screen">
            <Sidebar sections={sectionData} />

            <main className="flex-1 overflow-y-auto">
                <div className="max-w-4xl mx-auto px-4 py-16 lg:px-8">
                    {/* Hero Section */}
                    <div className="text-center mb-16 space-y-6">
                        <div className="inline-flex items-center justify-center w-20 h-20 bg-primary/10 rounded-2xl mb-4">
                            <BookOpen className="w-10 h-10 text-primary" />
                        </div>
                        <h1 className="text-5xl font-bold text-foreground">
                            Solidroad Managed Services Documentation
                        </h1>
                        <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
                            {totalDocs} documentation files
                        </p>
                    </div>

                    {/* Sections Grid */}
                    <div className="grid md:grid-cols-2 gap-6 mb-12">
                        <Link
                            href="/developer-guide/00_INDEX"
                            className="group p-8 bg-secondary border border-border rounded-2xl hover:border-primary hover:shadow-lg hover:shadow-primary/10 transition-all"
                        >
                            <div className="flex items-start justify-between mb-4">
                                <div className="p-3 bg-primary/10 rounded-xl group-hover:bg-primary/20 transition-colors">
                                    <Code className="w-6 h-6 text-primary" />
                                </div>
                                <ArrowRight className="w-5 h-5 text-muted-foreground group-hover:text-primary group-hover:translate-x-1 transition-all" />
                            </div>
                            <h2 className="text-2xl font-bold mb-2 group-hover:text-primary transition-colors">
                                Developer Guide
                            </h2>
                            <p className="text-muted-foreground mb-4">
                                Technical documentation for the team working on content pipelines and AI agents
                            </p>
                            <div className="text-sm text-muted-foreground">
                                {sectionData.find(s => s.name === 'developer-guide')?.docs.length || 0} documents
                            </div>
                        </Link>

                        <Link
                            href="/user-guide/QUICK_START"
                            className="group p-8 bg-secondary border border-border rounded-2xl hover:border-primary hover:shadow-lg hover:shadow-primary/10 transition-all"
                        >
                            <div className="flex items-start justify-between mb-4">
                                <div className="p-3 bg-primary/10 rounded-xl group-hover:bg-primary/20 transition-colors">
                                    <BookOpen className="w-6 h-6 text-primary" />
                                </div>
                                <ArrowRight className="w-5 h-5 text-muted-foreground group-hover:text-primary group-hover:translate-x-1 transition-all" />
                            </div>
                            <h2 className="text-2xl font-bold mb-2 group-hover:text-primary transition-colors">
                                Writer Guide
                            </h2>
                            <p className="text-muted-foreground mb-4">
                                Quick start guides and execution prompts for end users
                            </p>
                            <div className="text-sm text-muted-foreground">
                                {sectionData.find(s => s.name === 'user-guide')?.docs.length || 0} documents
                            </div>
                        </Link>
                    </div>
                </div>
            </main>
        </div>
    )
}
