/**
 * Open Library API Provider for NoteVault
 * 
 * Fetches textbooks and reference materials matching a user query.
 * Normalizes the output into NoteVault's Unified Resource Model.
 */
export async function searchTextbooks(query) {
  if (!query || query.trim() === '') return []

  try {
    const encodedQuery = encodeURIComponent(query)
    // We limit to 5 to keep the search fast and relevant
    const response = await fetch(`https://openlibrary.org/search.json?q=${encodedQuery}&limit=5`)
    
    if (!response.ok) {
      console.warn(`OpenLibrary API returned status: ${response.status}`)
      return [] 
    }

    const data = await response.json()
    
    if (!data.docs || !Array.isArray(data.docs)) return []

    return data.docs.map(book => ({
      id: `ol-${book.key.replace('/works/', '')}`,
      title: book.title,
      type: 'textbook',
      url: `https://openlibrary.org${book.key}`,
      description: book.first_publish_year ? `First published in ${book.first_publish_year}.` : 'Textbook / Reference Material',
      author_name: book.author_name ? book.author_name[0] : 'Unknown Author',
      isSaved: false,
      isExternal: true
    }))

  } catch (error) {
    console.error('Network error reaching Open Library API:', error)
    return []
  }
}
