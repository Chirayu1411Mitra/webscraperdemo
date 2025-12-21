async function scrapeNews() {
    const keyword = document.getElementById('keywordInput').value;
    const resultsDiv = document.getElementById('results');
    const loadingDiv = document.getElementById('loading');

    if (!keyword) {
        alert("Please enter a keyword or URL");
        return;
    }

    // Clear previous results
    resultsDiv.innerHTML = '';
    loadingDiv.classList.remove('hidden');

    try {
        const response = await fetch('/scrape', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ keyword: keyword, count: 20 })
        });

        const data = await response.json();

        console.log('Response status:', response.status);
        console.log('Response data:', data);

        if (response.ok) {
            console.log('Articles received:', data.results);
            displayResults(data.results, keyword);
        } else {
            resultsDiv.innerHTML = `<p style="color: red; text-align: center;">${data.message || data.error}</p>`;
        }
    } catch (error) {
        console.error('Error:', error);
        resultsDiv.innerHTML = `<p style="color: red; text-align: center;">An error occurred. Please try again.</p>`;
    } finally {
        loadingDiv.classList.add('hidden');
    }
}

function displayResults(articles, keyword) {
    const resultsDiv = document.getElementById('results');

    console.log('displayResults called with:', articles);
    console.log('Number of articles:', articles ? articles.length : 'articles is null/undefined');

    if (!articles || articles.length === 0) {
        resultsDiv.innerHTML = '<p>No results found.</p>';
        return;
    }

    articles.forEach((article, index) => {
        console.log(`Article ${index}:`, article);
        const card = document.createElement('div');
        card.className = 'card';

        const highlightParam = keyword ? `#:~:text=${encodeURIComponent(keyword)}` : '';
        card.innerHTML = `
            <h3>${article.title || 'No title'}</h3>
            <p>${article.summary || 'No summary available'}</p>
            <a href="${(article.url || '#') + highlightParam}" target="_blank" class="read-more">Read Full Article →</a>
        `;

        resultsDiv.appendChild(card);
    });
}

// Allow Enter key to trigger search
document.getElementById('keywordInput').addEventListener('keypress', function (e) {
    if (e.key === 'Enter') {
        scrapeNews();
    }
});
