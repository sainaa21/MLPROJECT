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


// =====================================
// SENTIMENT CHART
// =====================================

const sentimentChart =
new Chart(

    document.getElementById(
        "sentimentChart"
    ),

    {

        type: "pie",

        data: {

            labels: [
                "Positive",
                "Neutral",
                "Negative"
            ],

            datasets: [{

                data: [0,0,0],

                backgroundColor: [
                    "#00ff66",
                    "#ffaa00",
                    "#ff0000"
                ]
            }]
        }
    }
);


// =====================================
// SPAM CHART
// =====================================

const spamChart =
new Chart(

    document.getElementById(
        "spamChart"
    ),

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
                    "#ff0000",
                    "#555555"
                ]
            }]
        }
    }
);


// =====================================
// BUTTON CLICK
// =====================================

analyzeBtn.addEventListener(
    "click",
    analyzeVideo
);


// =====================================
// ANALYZE FUNCTION
// =====================================

async function analyzeVideo(){

    const url = videoUrl.value;

    if(url === ""){

        alert(
            "Please enter YouTube URL"
        );

        return;
    }

    try{

        const response =
        await fetch(

            "http://127.0.0.1:8000/analyze",

            {

                method: "POST",

                headers: {

                    "Content-Type":
                    "application/json"
                },

                body: JSON.stringify({

                    url: url
                })
            }
        );

        const data =
        await response.json();

        console.log(data);


        // =====================================
        // UPDATE TEXT
        // =====================================

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


        // =====================================
        // SUMMARY
        // =====================================

        if(summaryBox){

            summaryBox.innerText =
            data.summary;
        }


        // =====================================
        // UPDATE SENTIMENT CHART
        // =====================================

        sentimentChart.data.datasets[0].data = [

            data.good_comments,

            data.neutral_comments,

            data.bad_comments
        ];

        sentimentChart.update();


        // =====================================
        // UPDATE SPAM CHART
        // =====================================

        spamChart.data.datasets[0].data = [

            data.valid_comments,

            data.spam_comments
        ];

        spamChart.update();

    }

    catch(error){

        console.log(error);

        alert(
            "Backend connection failed"
        );
    }
}
// =====================================
// TREND CHART
// =====================================

const trendChart =
new Chart(

    document.getElementById(
        "trendChart"
    ),

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

                borderColor: "#ff0000",

                backgroundColor: "rgba(255,0,0,0.2)",

                tension: 0.4
            }]
        }
    }
);


// =====================================
// YEAR CHART
// =====================================

const yearChart =
new Chart(

    document.getElementById(
        "yearChart"
    ),

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
                    "#ff0000",
                    "#990000"
                ]
            }]
        }
    }
);