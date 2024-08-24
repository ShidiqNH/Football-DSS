const clubInput = document.getElementById('club');
const clubSuggestions = document.getElementById('club-suggestions');
const clubSuggestionList = document.getElementById('club-suggestion-list');

clubInput.addEventListener('input', function() {
    const query = this.value;
    if (query.length > 0) {
        fetch(`/api/suggestions?query=${query}&type=club`)
            .then(response => response.json())
            .then(data => {
                clubSuggestionList.innerHTML = '';
                data.forEach(club => {
                    const li = document.createElement('li');
                    li.textContent = club;
                    li.addEventListener('click', function() {
                        clubInput.value = club;
                        clubSuggestions.style.display = 'none';
                    });
                    clubSuggestionList.appendChild(li);
                });
                clubSuggestions.style.display = data.length > 0 ? 'block' : 'none';
            });
    } else {
        clubSuggestions.style.display = 'none';
    }
});

clubInput.addEventListener('focus', function() {
    if (clubSuggestionList.children.length > 0) {
        clubSuggestions.style.display = 'block';
    }
});

document.addEventListener('click', function(event) {
    if (!clubInput.contains(event.target) && !clubSuggestions.contains(event.target)) {
        clubSuggestions.style.display = 'none';
    }
});


document.getElementById('name').addEventListener('input', function() {
    const query = this.value;
    const suggestionsContainer = document.getElementById('player-suggestions');
    const suggestionsList = document.getElementById('player-suggestion-list');

    if (query.length > 2) {
        fetch(`/api/player_suggestions?name=${query}`)
            .then(response => response.json())
            .then(data => {
                suggestionsList.innerHTML = '';
                if (data.length > 0) {
                    suggestionsContainer.style.display = 'block';
                    data.forEach(player => {
                        const listItem = document.createElement('li');
                        listItem.innerHTML = `
                            <a href="/player/${player.Sofifa_ID}">
                                <img src="${player.Photo || '/static/img/empty-profile.png'}" alt="${player.Name}" class="player-photo">
                                ${player.Name}
                            </a>
                        `;
                        suggestionsList.appendChild(listItem);
                    });
                } else {
                    suggestionsContainer.style.display = 'none';
                }
            })
            .catch(error => console.error('Error fetching player suggestions:', error));
    } else {
        suggestionsContainer.style.display = 'none';
    }
});

document.addEventListener('click', function(e) {
    const suggestionsContainer = document.getElementById('player-suggestions');
    if (!suggestionsContainer.contains(e.target) && e.target.id !== 'name') {
        suggestionsContainer.style.display = 'none';
    }
});

