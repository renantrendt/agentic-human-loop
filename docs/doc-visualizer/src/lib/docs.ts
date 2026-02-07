import fs from 'fs'
import path from 'path'
import matter from 'gray-matter'

export interface DocMetadata {
    title: string
    slug: string
    section: string
    order?: number
}

export interface Doc extends DocMetadata {
    content: string
}

const DOCS_BASE_PATH = path.join(process.cwd(), '..')

export function getDocSections(): string[] {
    return ['user-guide', 'developer-guide']
}

export function getDocsForSection(section: string): DocMetadata[] {
    const sectionPath = path.join(DOCS_BASE_PATH, section)

    if (!fs.existsSync(sectionPath)) {
        return []
    }

    const files = fs.readdirSync(sectionPath)
    const mdFiles = files.filter(file => file.endsWith('.md'))

    return mdFiles.map(file => {
        const filePath = path.join(sectionPath, file)
        const fileContents = fs.readFileSync(filePath, 'utf8')
        const { data } = matter(fileContents)

        return {
            title: data.title || file.replace('.md', '').replace(/_/g, ' '),
            slug: file.replace('.md', ''),
            section,
            order: data.order,
        }
    }).sort((a, b) => {
        // Sort by order if available, otherwise alphabetically by filename
        if (a.order !== undefined && b.order !== undefined) {
            return a.order - b.order
        }
        return a.slug.localeCompare(b.slug)
    })
}

export function getDoc(section: string, slug: string): Doc | null {
    const filePath = path.join(DOCS_BASE_PATH, section, `${slug}.md`)

    if (!fs.existsSync(filePath)) {
        return null
    }

    const fileContents = fs.readFileSync(filePath, 'utf8')
    const { data, content } = matter(fileContents)

    return {
        title: data.title || slug.replace(/_/g, ' '),
        slug,
        section,
        order: data.order,
        content,
    }
}

export function getAllDocs(): Doc[] {
    const sections = getDocSections()
    const allDocs: Doc[] = []

    sections.forEach(section => {
        const docs = getDocsForSection(section)
        docs.forEach(docMeta => {
            const doc = getDoc(section, docMeta.slug)
            if (doc) {
                allDocs.push(doc)
            }
        })
    })

    return allDocs
}
