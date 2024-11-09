
//newsapi
document.getElementById('fetchBtn').addEventListener('click', async () => {
    const country = document.getElementById('country').value;
    const category = document.getElementById('category').value;

    try {
        const response = await fetch(`http://localhost:5001/api/news?country=${country}&category=${category}`);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();

        // Display results in table
        const resultsTable = document.getElementById('resultsTable').getElementsByTagName('tbody')[0];
        resultsTable.innerHTML = ''; // Clear previous results

        if (data.sentiment_analysis) {
            for (const [topic, sentimentData] of Object.entries(data.sentiment_analysis)) {
                const newRow = resultsTable.insertRow();
                
                // Get keywords associated with the current topic
                const keywords = data.topics[topic] || [];
                newRow.insertCell(0).textContent = `${topic}: [${keywords.join(', ')}]`;
                
                // Format sentiment and average polarity
                const averagePolarity = sentimentData.average_polarity?.toFixed(2);
                newRow.insertCell(1).textContent = `${sentimentData.sentiment} (${averagePolarity})`;
            }
        } else {
            console.log('No sentiment analysis data found.');
        }

        // Display Word Cloud image
        document.getElementById('wordcloud').src = `data:image/png;base64,${data.wordcloud_image}`;

        // Prepare data for donut chart
        const sentimentCounts = data.sentiment_counts;
        const labels = Object.keys(sentimentCounts);
        const values = Object.values(sentimentCounts);

        const donutData = [{
            values: values,
            labels: labels,
            type: 'pie',
            hole: 0.4,
            marker: {
                colors: ['#ff9999','#66b3ff','#99ff99'] // Adjust colors as needed
            },
            textinfo: 'percent',
            textposition: 'inside',
        }];

        const layout = {
            width: 300,
            height: 150,
            showlegend: true,
            margin: { t: 20, b: 20 }
        };

        // Render donut chart
        Plotly.newPlot('donut-chart', donutData, layout);
        
    } catch (error) {
        console.error('Error fetching data:', error);
    }
});


async function fetchForecast() {
    const keyword = document.getElementById('forecast-keyword').value;
    const timeframe = document.getElementById('forecast-timeframe').value;
    if (!keyword) {
        alert("Please enter a keyword.");
        return;
    }

    try {
        // Send request to Flask API for forecast data
        const response = await fetch('http://localhost:5002/api/forecast_data', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                keyword: keyword,
                timeframe: timeframe
            })
        });

        const data = await response.json();
        if (data.error) {
            alert(data.error);
            return;
        }

        const originalData = JSON.parse(data.original_data);
        const forecastData = JSON.parse(data.forecast);

        // Prepare Plotly traces for original data and forecast
        const traceOriginal = {
            x: originalData.map(d => new Date(d.date)),
            y: originalData.map(d => d[Object.keys(d)[1]]), // Access second column (interest level)
            mode: 'lines',
            name: 'Original Data',
            line: { color: '#66b3ff' }
        };

        // Get the last date of the original data
        const lastOriginalDate = new Date(originalData[originalData.length - 1].date);
        // Adjust the forecast data to start after the last date of the original data
        const forecastStartDate = new Date(lastOriginalDate);
        forecastStartDate.setDate(forecastStartDate.getDate() + 1); // Start from the next day after the last original date

        // Filter the forecast data to only include values after the last original data date
        const filteredForecastData = forecastData.filter(d => new Date(d.ds) >= forecastStartDate);

        // Prepare forecast trace to start from the last date of original data
        const traceForecast = {
            x: filteredForecastData.map(d => new Date(d.ds)),
            y: filteredForecastData.map(d => d.yhat),
            mode: 'lines',
            name: 'Forecast',
            line: { color: '#ff9999' } 
        };

        // Combine the original data and forecast data
        const combinedData = [traceOriginal, traceForecast];

        // Layout configuration
        const layout = {
            title: `Interest Over Time for "${keyword}"`,
            xaxis: {
                title: 'Date',
                tickformat: "%Y-%m", // Show year and month on x-axis
                tickmode: 'auto'
            },
            yaxis: { title: 'Interest Level' },
            showlegend: true
        };

        // Render the plot using Plotly
        Plotly.newPlot('forecastPlot', combinedData, layout);

    } catch (error) {
        console.error('Error fetching forecast data:', error);
        alert('Error fetching forecast data.');
    }
}

async function fetchInterest() {
    const keywords = [];
    const keywordInputs = document.querySelectorAll('.interest-input-box'); // Select all input fields with the class 'input-box'
    console.log(keywordInputs);
    // Collect keywords from the input fields
    keywordInputs.forEach(input => {
        if (input.value.trim() !== '') {
            keywords.push(input.value.trim());
        }
    });
    console.log(keywords)
    // Ensure there are between 1 and 5 keywords
    if (keywords.length < 1 || keywords.length > 5) {
        alert("Please enter between 1 and 5 keywords.");
        return;
    }

    const timeframe = document.getElementById('interest-timeframe').value;

    // Array of colors for the lines
    const colors = ['#ff9999','#66b3ff','#99ff99' , 'purple'];

    try {
        // Send request to Flask API for interest data
        const response = await fetch('http://localhost:5002/api/interest_data', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                keyword: keywords,
                timeframe: timeframe
            
            })
        });

        const data = await response.json();
        const dates = data.map(item => item.date);

        // Prepare traces for Plotly
        const traces = keywords.map((keyword, index) => {
            return {
                x: dates,
                y: data.map(item => item[keyword]),
                type: 'scatter',
                mode: 'lines',
                name: keyword,
                line: { color: colors[index] } // Assign color based on index
            };
        });
        console.log(keywords)
        const layout = {
            title: `Interest Over Time Comparison for : <br>${keywords.join(', ')}`,
            xaxis: { title: "Date" },
            yaxis: { title: "Interest Level" },
            showlegend: true
        };

        // Plot using Plotly
        Plotly.newPlot('interestPlot', traces, layout);
    } catch (error) {
        console.error('Error fetching interest data:', error);
        alert('Error fetching interest data.');
    }
}



function fetchGrowthRate() {
    const keyword = document.getElementById('growth-keyword').value.trim();
    const timeframe = document.getElementById('growth-timeframe').value;
    const growthRateText = document.getElementById('growth-rate-text');
    const growthRatePercentage = document.getElementById('growth-rate-percentage');

    if (!keyword) {
        alert("Please enter a single keyword.");
        return;
    }

    fetch('http://127.0.0.1:5002/api/growth_rate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ keyword, timeframe })
    })
    .then(response => response.json())
    .then(data => {
        // Set the growth rate percentage in large font
        growthRatePercentage.textContent = data.compound_growth_rate || "N/A";
        growthRateText.textContent = data.indication || "Growth rate data unavailable.";
    })
    .catch(error => {
        console.error("Error fetching growth rate:", error);
        growthRateText.textContent = "Error fetching growth rate data.";
        growthRatePercentage.textContent = "";
    });
}

// Function to gather info and send it to Flask API
async function selectContentType(contentType) {
    const brandInfo = document.getElementById('brandInfo').value;
    const country = document.getElementById('country').value;
    const category = document.getElementById('category').value;

    if (!brandInfo) {
        alert("Please enter brand information.");
        return;
    }

    // Step 1: Gather brand info
    const gatherInfoResponse = await fetch('http://127.0.0.1:5003/api/gather_info', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ brand_info: brandInfo, content_type: contentType, country: country, category: category })
    });
    const gatherInfoData = await gatherInfoResponse.json();
    if (gatherInfoData.error) {
        alert(gatherInfoData.error);
        return;
    }

    // Clear previous content
    document.getElementById('content').innerHTML = '';
    document.getElementById('content').innerHTML += `<h2>Generating ${contentType.replace('_', ' ')} for brand...</h2>`;

    // Step 2: Generate content and stream it
    fetchContentStream(brandInfo, contentType, country, category);
}

// Function to handle streaming content
async function fetchContentStream(brandInfo, contentType, country, category) {
    const response = await fetch('http://127.0.0.1:5003/api/generate_content', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ brand_info: brandInfo, content_type: contentType, country: country, category: category })
    });

    // Check if the response is okay
    if (!response.ok) {
        document.getElementById('content').innerHTML = "Error generating content. Please try again.";
        return;
    }

    // Process the streaming response
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let contentSection = null;
    let topicCounter = 1;

    while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        
        // If new topic, create a new section
        if (chunk.includes("Topic")) {
            contentSection = document.createElement('div');
            contentSection.className = 'content-section';
            contentSection.innerHTML = `<h3>Topic ${topicCounter}</h3>`;
            document.getElementById('content').appendChild(contentSection);
            topicCounter++;
        }

        // Append text to the current content section
        if (contentSection) {
            if(chunk.includes('\n')){
                contentSection.innerHTML += '<br><br>';
            }
            else{
                contentSection.innerHTML += `<span>${chunk}</span>`;
            }
        }
    }
}

document.addEventListener("DOMContentLoaded", function() {
    const currentPage = window.location.pathname.split("/").pop(); // Get current page filename
    const sidebarLinks = document.querySelectorAll(".sidebar a");

    sidebarLinks.forEach(link => {
        if (link.getAttribute("href") === currentPage) {
            link.classList.add("active"); // Add active class to the current page link
        }
    });
});
        // Fetch keyword suggestions from Flask API and display them as bubbles
function fetchSuggestions() {
            const keyword = document.getElementById("keyword-input").value;
            fetch(`http://127.0.0.1:5002/api/keyword_suggestions?keyword=${keyword}`)
                .then(response => response.json())
                .then(data => {
                    const container = document.getElementById("bubble-container");
                    container.innerHTML = ""; // Clear previous bubbles
                    
                    // Create a bubble for each title
                    data.titles.forEach(title => {
                        const bubble = document.createElement("div");
                        bubble.className = "bubble";
                        bubble.innerText = title;
                        container.appendChild(bubble);
                    });
                });
        }