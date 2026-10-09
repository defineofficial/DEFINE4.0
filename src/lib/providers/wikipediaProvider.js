export const searchWikipedia = async (query) => {
  try {
    const encodedQuery = encodeURIComponent(query)
    // Wikipedia API for searching articles
    const response = await fetch(`https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch=${encodedQuery}&utf8=&format=json&origin=*`)
    
    if (!response.ok) {
      throw new Error('Wikipedia API failed')
    }

    const data = await response.json()
    const searchResults = data.query?.search || []
    
    return searchResults.map(item => {
      // Create a clean snippet by stripping HTML tags from the Wikipedia snippet
      const cleanSnippet = item.snippet.replace(/<\/?[^>]+(>|$)/g, "")
      
      // We label Wikipedia articles as 'note'
      return {
        id: `wiki-${item.pageid}`,
        title: item.title,
        type: 'note',
        url: `https://en.wikipedia.org/?curid=${item.pageid}`,
        description: cleanSnippet + '...',
        author_name: 'Wikipedia',
        created_at: item.timestamp,
        isExternal: true,
        isSaved: false
      }
    })
  } catch (error) {
    console.error('Error fetching from Wikipedia:', error)
    return [] // Return empty array on failure
  }
}
