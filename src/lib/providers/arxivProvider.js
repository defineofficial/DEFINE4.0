export const searchArxiv = async (query) => {
  try {
    const encodedQuery = encodeURIComponent(query)
    // arXiv API uses atom+xml format. We fetch up to 10 results.
    const response = await fetch(`https://export.arxiv.org/api/query?search_query=all:${encodedQuery}&start=0&max_results=8`)
    
    if (!response.ok) {
      throw new Error('ArXiv API failed')
    }

    const xmlText = await response.text()
    
    // Parse XML in the browser
    const parser = new DOMParser()
    const xmlDoc = parser.parseFromString(xmlText, "text/xml")
    
    const entries = Array.from(xmlDoc.getElementsByTagName("entry"))
    
    return entries.map(entry => {
      const title = entry.getElementsByTagName("title")[0]?.textContent?.trim() || "Untitled PDF"
      const summary = entry.getElementsByTagName("summary")[0]?.textContent?.trim() || ""
      const author = entry.getElementsByTagName("author")[0]?.getElementsByTagName("name")[0]?.textContent || "Unknown Author"
      const published = entry.getElementsByTagName("published")[0]?.textContent || new Date().toISOString()
      
      // Find the PDF link
      const links = Array.from(entry.getElementsByTagName("link"))
      const pdfLink = links.find(link => link.getAttribute("title") === "pdf")
      const url = pdfLink ? pdfLink.getAttribute("href") : entry.getElementsByTagName("id")[0]?.textContent
      
      // We label academic papers from arXiv as 'pdf'
      return {
        id: `arxiv-${Math.random().toString(36).substr(2, 9)}`,
        title: title,
        type: 'pdf',
        url: url,
        description: summary.substring(0, 300) + (summary.length > 300 ? '...' : ''),
        author_name: author,
        created_at: published,
        isExternal: true,
        isSaved: false
      }
    })
  } catch (error) {
    console.error('Error fetching from ArXiv:', error)
    return [] // Return empty array on failure so it doesn't break the whole search
  }
}
