/**
 * GitHub Search API Provider for NoteVault
 * 
 * Fetches engineering-related repositories matching a user query.
 * Normalizes the output into NoteVault's Unified Resource Model.
 */
export async function searchGithub(query) {
  if (!query || query.trim() === '') return []

  try {
    // We add topic:engineering to keep results relevant to the platform
    const encodedQuery = encodeURIComponent(`${query} topic:engineering`)
    const response = await fetch(`https://api.github.com/search/repositories?q=${encodedQuery}&sort=stars&order=desc&per_page=10`)
    
    if (!response.ok) {
      if (response.status === 403) {
        console.warn('GitHub API rate limit exceeded.')
      } else {
        console.warn(`GitHub API returned status: ${response.status}`)
      }
      return [] // Graceful degradation
    }

    const data = await response.json()
    
    if (!data.items || !Array.isArray(data.items)) return []

    return data.items.map(repo => ({
      id: `gh-${repo.id}`,
      title: repo.full_name,
      type: 'github',
      url: repo.html_url,
      description: repo.description || 'No description provided.',
      author_name: repo.owner?.login || 'Unknown',
      isSaved: false, // Default for external results
      isExternal: true // Flag to tell the UI this isn't in our DB yet
    }))

  } catch (error) {
    console.error('Network error reaching GitHub API:', error)
    return []
  }
}
