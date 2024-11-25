document.addEventListener('DOMContentLoaded', () => {
    // Initialize Lucide icons
    lucide.createIcons();

    // Chat elements
    const chatForm = document.getElementById('chatForm');
    const userInput = document.getElementById('userInput');
    const chatContainer = document.getElementById('chatContainer');
    const itinerarySection = document.getElementById('itinerarySection');

    // Function to get welcome message
    async function getWelcomeMessage(languageCode) {
        try {
            const response = await fetch('/api/create-itinerary', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    preferences: `SYSTEM:LANGUAGE=${languageCode}`,
                    duration: null,
                    budget: null
                })
            });

            if (!response.ok) {
                throw new Error('Failed to get welcome message');
            }

            const data = await response.json();
            return data.itinerary[0].activities[0];
        } catch (error) {
            console.error('Error getting welcome message:', error);
            return "Welcome to Dubai Tourism Assistant! How can I help you plan your trip?";
        }
    }

    // Add this function to show typing indicator
    function showTypingIndicator() {
        const typingDiv = document.createElement('div');
        typingDiv.className = 'flex items-start justify-start mb-4';
        typingDiv.innerHTML = `
            <div class="mr-2 flex-shrink-0">
                <div class="h-8 w-8 rounded-full overflow-hidden">
                    <img src="https://hebbkx1anhila5yf.public.blob.vercel-storage.com/image-jOhLU28iALz0Huxz2QAeCmn2So9U0G.png" 
                         alt="Assistant" 
                         class="h-full w-full object-cover">
                </div>
            </div>
            <div class="typing-indicator">
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
            </div>
        `;
        chatContainer.appendChild(typingDiv);
        return typingDiv;
    }

    // Handle form submission
    chatForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const message = userInput.value.trim();
        if (!message) return;

        // Add user message
        addMessage(message, true);
        userInput.value = '';
        userInput.disabled = true;

        // Show typing indicator
        const typingDiv = document.createElement('div');
        typingDiv.className = 'flex items-start justify-start mb-4';
        typingDiv.innerHTML = `
            <div class="mr-2 flex-shrink-0">
                <div class="h-8 w-8 rounded-full overflow-hidden">
                    <img src="https://hebbkx1anhila5yf.public.blob.vercel-storage.com/image-jOhLU28iALz0Huxz2QAeCmn2So9U0G.png" 
                         alt="Assistant" 
                         class="h-full w-full object-cover">
                </div>
            </div>
            <div class="typing-indicator">
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
            </div>
        `;
        chatContainer.appendChild(typingDiv);

        try {
            // Add artificial delay
            await new Promise(resolve => setTimeout(resolve, 1000));

            const response = await fetch('/api/create-itinerary', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    preferences: message,
                    duration: null,
                    budget: null
                })
            });

            if (!response.ok) throw new Error('Failed to get response');

            const data = await response.json();
            
            // Remove typing indicator
            typingDiv.remove();
            
            if (data.itinerary[0].day === 0) {
                addMessage(data.itinerary[0].activities[0], false);
            } else {
                addMessage("I've created your personalized Dubai itinerary! You can now view it!", false);
                displayItinerary(data);
                itinerarySection?.classList.remove('hidden');
            }
        } catch (error) {
            // Remove typing indicator
            typingDiv.remove();
            
            console.error('Error:', error);
            addMessage('Sorry, I encountered an error. Please try again.', false);
        } finally {
            userInput.disabled = false;
            userInput.focus();
        }
    });

    // Add message to chat
    function addMessage(content, isUser = false) {
        if (!chatContainer || !content) return;

        // For user messages or simple string responses
        if (isUser || typeof content === 'string') {
            const messageDiv = document.createElement('div');
            messageDiv.className = `flex items-start ${isUser ? 'justify-end' : 'justify-start'} mb-4`;
            
            const messageContent = `
                ${!isUser ? `
                    <div class="mr-2 flex-shrink-0">
                        <div class="h-8 w-8 rounded-full overflow-hidden">
                            <img src="https://hebbkx1anhila5yf.public.blob.vercel-storage.com/image-jOhLU28iALz0Huxz2QAeCmn2So9U0G.png" 
                                 alt="Assistant" 
                                 class="h-full w-full object-cover">
                        </div>
                    </div>
                ` : ''}
                <div class="max-w-[70%] rounded-lg p-3 ${isUser ? 'bg-[#c41e3a]' : 'bg-[#007acc]'} text-white">
                    <p class="text-sm">${content}</p>
                </div>
                ${isUser ? `
                    <div class="ml-2 flex-shrink-0">
                        <div class="h-8 w-8 rounded-full bg-[#c41e3a] flex items-center justify-center">
                            <i data-lucide="user" class="h-5 w-5 text-white"></i>
                        </div>
                    </div>
                ` : ''}
            `;

            messageDiv.innerHTML = messageContent;
            chatContainer.appendChild(messageDiv);
        } 
        // For AI responses with itinerary and hotel suggestion
        else {
            // First, display hotel suggestion if present
            if (content.hotel_suggestion) {
                const hotelDiv = document.createElement('div');
                hotelDiv.className = 'flex items-start justify-start mb-4';
                
                const hotelContent = `
                    <div class="mr-2 flex-shrink-0">
                        <div class="h-8 w-8 rounded-full overflow-hidden">
                            <img src="https://hebbkx1anhila5yf.public.blob.vercel-storage.com/image-jOhLU28iALz0Huxz2QAeCmn2So9U0G.png" 
                                 alt="Assistant" 
                                 class="h-full w-full object-cover">
                        </div>
                    </div>
                    <div class="max-w-[70%] rounded-lg p-4 bg-white shadow-lg">
                        <h3 class="text-lg font-bold text-[#007acc] mb-2">Recommended Hotel</h3>
                        <div class="space-y-2">
                            <p class="font-semibold text-gray-800">${content.hotel_suggestion.NAME}</p>
                            <p class="text-sm text-[#E81D52]">${content.hotel_suggestion.CATEGORY}</p>
                            <p class="text-sm text-gray-600">📍 ${content.hotel_suggestion.LOCATION}</p>
                            <p class="text-sm font-medium text-[#E81D52]">${content.hotel_suggestion.PRICE}</p>
                            <p class="text-sm text-gray-600">✨ ${content.hotel_suggestion.AMENITIES}</p>
                            <p class="text-sm text-gray-700">${content.hotel_suggestion.DESCRIPTION}</p>
                            <p class="text-sm font-medium">⭐ Rating: ${content.hotel_suggestion.RATING}</p>
                        </div>
                    </div>
                `;
                
                hotelDiv.innerHTML = hotelContent;
                chatContainer.appendChild(hotelDiv);
            }

            // Then display the itinerary message
            if (content.itinerary && content.itinerary[0]) {
                const messageDiv = document.createElement('div');
                messageDiv.className = 'flex items-start justify-start mb-4';
                
                const messageContent = `
                    <div class="mr-2 flex-shrink-0">
                        <div class="h-8 w-8 rounded-full overflow-hidden">
                            <img src="https://hebbkx1anhila5yf.public.blob.vercel-storage.com/image-jOhLU28iALz0Huxz2QAeCmn2So9U0G.png" 
                                 alt="Assistant" 
                                 class="h-full w-full object-cover">
                        </div>
                    </div>
                    <div class="max-w-[70%] rounded-lg p-3 bg-[#007acc] text-white">
                        <p class="text-sm">${content.itinerary[0].activities[0]}</p>
                    </div>
                `;

                messageDiv.innerHTML = messageContent;
                chatContainer.appendChild(messageDiv);
            }
        }

        // Initialize icons and scroll to bottom
        lucide.createIcons({
            icons: {
                user: true
            }
        });
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }

    // Initialize chat with welcome message
    getWelcomeMessage('en').then(welcomeMessage => {
        addMessage(welcomeMessage);
    });

    // Add this function after your existing functions
    function displayItinerary(data) {
        const itineraryContainer = document.getElementById('itineraryContainer');
        if (!itineraryContainer || !data || !data.itinerary) return;

        let html = '';

        // Display hotel suggestion first if available
        if (data.hotel_suggestion) {
            html += `
                <div class="mb-8 bg-white rounded-lg shadow-lg overflow-hidden">
                    <div class="bg-gradient-to-r from-[#E81D52] to-[#c41e3a] p-4">
                        <h2 class="text-xl font-bold text-white flex items-center">
                            <i data-lucide="hotel" class="h-6 w-6 mr-2"></i>
                            Recommended Hotel
                        </h2>
                    </div>
                    <div class="p-6">
                        <div class="grid md:grid-cols-[1fr_2fr] gap-6">
                            <div class="relative h-48 rounded-xl overflow-hidden shadow-md">
                                <img 
                                    src="https://hebbkx1anhila5yf.public.blob.vercel-storage.com/dubai-placeholder.jpg" 
                                    alt="${data.hotel_suggestion.NAME}"
                                    class="object-cover w-full h-full transition-transform duration-300 hover:scale-105"
                                />
                                <div class="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent"></div>
                                <div class="absolute bottom-4 left-4 bg-white/90 px-3 py-1 rounded-full text-sm font-medium text-[#E81D52]">
                                    ${data.hotel_suggestion.PRICE}
                                </div>
                            </div>
                            <div class="flex flex-col justify-between">
                                <div>
                                    <div class="flex items-center gap-2 mb-2">
                                        <span class="text-sm font-medium text-[#E81D52]">${data.hotel_suggestion.CATEGORY}</span>
                                        <span class="text-sm font-medium">⭐ ${data.hotel_suggestion.RATING}</span>
                                    </div>
                                    <h3 class="text-xl font-semibold text-gray-900 mb-2">
                                        ${data.hotel_suggestion.NAME}
                                    </h3>
                                    <p class="text-gray-600 mb-3 leading-relaxed">${data.hotel_suggestion.DESCRIPTION}</p>
                                    <div class="flex items-center gap-1 text-sm text-gray-500 mb-2">
                                        <i data-lucide="map-pin" class="h-4 w-4"></i>
                                        <span>${data.hotel_suggestion.LOCATION}</span>
                                    </div>
                                    <div class="flex items-center gap-1 text-sm text-gray-500">
                                        <i data-lucide="check" class="h-4 w-4 text-[#E81D52]"></i>
                                        <span>${data.hotel_suggestion.AMENITIES}</span>
                                    </div>
                                </div>
                                <button class="mt-4 w-full bg-[#E81D52] text-white px-4 py-2 rounded-md hover:bg-[#d41848] transition-all duration-200 transform hover:-translate-y-0.5 focus:outline-none focus:ring-2 focus:ring-[#E81D52] focus:ring-opacity-50">
                                    Book Hotel
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        }

        // Process each day
        data.itinerary.forEach((day, index) => {
            if (day.day === 0) return; // Skip system messages

            html += `
                <div class="mb-8 bg-white rounded-lg shadow-lg overflow-hidden">
                    <div class="bg-gradient-to-r from-[#007acc] to-[#0056b3] p-4">
                        <h2 class="text-xl font-bold text-white flex items-center">
                            <i data-lucide="calendar" class="h-6 w-6 mr-2"></i>
                            Day ${day.day}
                        </h2>
                    </div>
                    <div class="divide-y divide-gray-200">
            `;

            // Process activities for this day
            const processedActivities = processActivities(day.activities);
            
            processedActivities.forEach(activity => {
                html += `
                    <div class="p-6 hover:bg-gray-50 transition-colors duration-200">
                        <div class="grid md:grid-cols-[1fr_2fr] gap-6">
                            <div class="relative h-48 rounded-xl overflow-hidden shadow-md">
                                <img 
                                    src="https://hebbkx1anhila5yf.public.blob.vercel-storage.com/dubai-placeholder.jpg" 
                                    alt="${activity.title}"
                                    class="object-cover w-full h-full transition-transform duration-300 hover:scale-105"
                                />
                                <div class="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent"></div>
                                <div class="absolute bottom-4 left-4 bg-white/90 px-3 py-1 rounded-full text-sm font-medium text-[#E81D52]">
                                    ${activity.price}
                                </div>
                            </div>
                            <div class="flex flex-col justify-between">
                                <div>
                                    <div class="flex items-center gap-2 mb-2">
                                        <i data-lucide="clock" class="h-4 w-4 text-[#E81D52]"></i>
                                        <span class="text-sm font-medium text-[#E81D52]">${activity.time}</span>
                                    </div>
                                    <h3 class="text-xl font-semibold text-gray-900 mb-2">
                                        ${activity.title}
                                    </h3>
                                    <p class="text-gray-600 mb-3 leading-relaxed">${activity.description}</p>
                                    <div class="flex items-center gap-1 text-sm text-gray-500">
                                        <i data-lucide="map-pin" class="h-4 w-4"></i>
                                        <span>${activity.location}</span>
                                    </div>
                                </div>
                                <button class="mt-4 w-full bg-[#E81D52] text-white px-4 py-2 rounded-md hover:bg-[#d41848] transition-all duration-200 transform hover:-translate-y-0.5 focus:outline-none focus:ring-2 focus:ring-[#E81D52] focus:ring-opacity-50">
                                    Book Activity
                                </button>
                            </div>
                        </div>
                    </div>
                `;
            });

            html += `
                    </div>
                </div>
            `;
        });

        // Add recommendations section
        if (data.recommendations && data.recommendations.length > 0) {
            html += generateRecommendationsHTML(data.recommendations);
        }

        itineraryContainer.innerHTML = html;
        lucide.createIcons();
    }

    function processActivities(activities) {
        const processedActivities = [];
        let currentActivity = null;
        let activityText = '';

        activities.forEach(line => {
            if (line.includes('TIME:')) {
                if (currentActivity) {
                    processedActivities.push(currentActivity);
                }
                currentActivity = {
                    time: '',
                    title: '',
                    description: '',
                    location: '',
                    price: ''
                };
                activityText = line;
            } else {
                activityText += '\n' + line;
            }

            if (currentActivity) {
                const timeMatch = activityText.match(/TIME: (.*?)(?=\n|$)/);
                const titleMatch = activityText.match(/TITLE: (.*?)(?=\n|$)/);
                const descriptionMatch = activityText.match(/DESCRIPTION: (.*?)(?=\n|$)/);
                const locationMatch = activityText.match(/LOCATION: (.*?)(?=\n|$)/);
                const priceMatch = activityText.match(/PRICE: (.*?)(?=\n|$)/);

                currentActivity.time = timeMatch ? timeMatch[1].trim() : 'Time TBD';
                currentActivity.title = titleMatch ? titleMatch[1].trim() : 'Activity';
                currentActivity.description = descriptionMatch ? descriptionMatch[1].trim() : 'No description available';
                currentActivity.location = locationMatch ? locationMatch[1].trim() : 'Location TBD';
                currentActivity.price = priceMatch ? priceMatch[1].trim() : 'Price on request';
            }
        });

        if (currentActivity) {
            processedActivities.push(currentActivity);
        }

        return processedActivities;
    }

    function generateRecommendationsHTML(recommendations) {
        return `
            <div class="mt-8 bg-white rounded-lg shadow-lg overflow-hidden">
                <div class="bg-gradient-to-r from-[#007acc] to-[#0056b3] p-4">
                    <h3 class="flex items-center text-xl font-bold text-white">
                        <i data-lucide="lightbulb" class="mr-2 h-6 w-6"></i>
                        Travel Tips & Recommendations
                    </h3>
                </div>
                <div class="p-6">
                    <ul class="space-y-3">
                        ${recommendations.map(tip => `
                            <li class="flex items-start">
                                <i data-lucide="check-circle" class="h-5 w-5 text-[#007acc] mr-2 flex-shrink-0 mt-0.5"></i>
                                <span class="text-gray-700">${tip.replace(/^- /, '')}</span>
                            </li>
                        `).join('')}
                    </ul>
                </div>
            </div>
        `;
    }
});