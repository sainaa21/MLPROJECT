const analyzeBtn =
document.getElementById("analyzeBtn");

const videoUrl =
document.getElementById("videoUrl");

const totalComments =
document.getElementById("totalComments");

const validComments =
document.getElementById("validComments");

const spamComments =
document.getElementById("spamComments");

const validityRate =
document.getElementById("validityRate");

const goodComments =
document.getElementById("goodComments");

const neutralComments =
document.getElementById("neutralComments");

const badComments =
document.getElementById("badComments");

const validPercent =
document.getElementById("validPercent");

const spamPercent =
document.getElementById("spamPercent");

const summaryBox =
document.getElementById("summaryBox");

analyzeBtn.addEventListener(
    "click",
    analyzeVideo
);

async function analyzeVideo(){

    const url = videoUrl.value;

    if(url === ""){

        alert("Please enter YouTube URL");

        return;
    }

    try{

        const response = await fetch(
            "http://127.0.0.1:8000/analyze",
            {
                method: "POST",

                headers:{
                    "Content-Type":
                    "application/json"
                },

                body: JSON.stringify({
                    url: url
                })
            }
        );

        const data = await response.json();

        console.log(data);

        totalComments.innerText =
        data.total_comments;

        validComments.innerText =
        data.valid_comments;

        spamComments.innerText =
        data.spam_comments;

        validityRate.innerText =
        data.validity_rate + "%";

        goodComments.innerText =
        data.good_comments;

        neutralComments.innerText =
        data.neutral_comments;

        badComments.innerText =
        data.bad_comments;

        validPercent.innerText =
        data.validity_rate + "%";

        spamPercent.innerText =
        data.spam_rate + "%";

        summaryBox.innerText =
        data.summary;

        sentimentChart.data.datasets[0].data = [
            data.good_comments,
            data.neutral_comments,
            data.bad_comments
        ];

        sentimentChart.update();

        spamChart.data.datasets[0].data = [
            data.valid_comments,
            data.spam_comments
        ];

        spamChart.update();

    }

    catch(error){

        console.log(error);

        alert("Error connecting to backend");
    }
}

const sentimentCtx =
document.getElementById(
    "sentimentChart"
);

const sentimentChart = new Chart(
    sentimentCtx,
    {

        type: "pie",

        data: {

            labels: [
                "Good",
                "Neutral",
                "Bad"
            ],

            datasets: [{

                data: [0,0,0],

                backgroundColor: [
                    "#4CAF50",
                    "#FFA500",
                    "#FF4C4C"
                ]

            }]
        },

        options: {

            responsive: true
        }
    }
);

const spamCtx =
document.getElementById(
    "spamChart"
);

const spamChart = new Chart(
    spamCtx,
    {

        type: "doughnut",

        data: {

            labels: [
                "Valid",
                "Spam"
            ],

            datasets: [{

                data: [0,0],

                backgroundColor: [
                    "#36A2EB",
                    "#C0C0C0"
                ]

            }]
        },

        options: {

            responsive: true
        }
    }
);

const trendCtx =
document.getElementById(
    "trendChart"
);

new Chart(
    trendCtx,
    {

        type: "line",

        data: {

            labels: [
                "Jan",
                "Feb",
                "Mar",
                "Apr",
                "May"
            ],

            datasets: [{

                label: "Views",

                data: [
                    12000,
                    18000,
                    25000,
                    22000,
                    19000
                ],

                borderColor: "#4CAF50",

                tension: 0.4
            }]
        },

        options: {

            responsive: true
        }
    }
);

const yearCtx =
document.getElementById(
    "yearChart"
);

new Chart(
    yearCtx,
    {

        type: "bar",

        data: {

            labels: [
                "2024",
                "2025"
            ],

            datasets: [{

                label: "Average Views",

                data: [
                    28000,
                    19000
                ],

                backgroundColor: [
                    "#2196F3",
                    "#2196F3"
                ]

            }]
        },

        options: {

            responsive: true
        }
    }
);