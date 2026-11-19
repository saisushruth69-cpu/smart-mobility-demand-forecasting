document.addEventListener("DOMContentLoaded", () => {

    const $ = id => document.getElementById(id);

    // -----------------------------
    // Slider values
    // -----------------------------
    [["temp", "tempOut"],
     ["atemp", "atempOut"],
     ["hum", "humOut"],
     ["windspeed", "windOut"]].forEach(([inputId, outputId]) => {

        const input = $(inputId);
        const output = $(outputId);

        if (input && output) {
            const update = () => {
                output.textContent = Number(input.value).toFixed(2);
            };

            input.addEventListener("input", update);
            update();
        }
    });


    // -----------------------------
    // PREDICTION
    // -----------------------------
    $("predictionForm").addEventListener("submit", async (e) => {

        e.preventDefault();

        const button = document.querySelector(".predict-btn");
        const error = $("error");

        error.textContent = "";

        button.disabled = true;
        button.innerHTML = "<span>⏳</span> Predicting...";

        const payload = {
            year: Number($("year").value),
            season: Number($("season").value),
            month: Number($("month").value),
            hour: Number($("hour").value),
            weekday: Number($("weekday").value),
            holiday: Number($("holiday").value),
            workingday: Number($("workingday").value),
            weathersit: Number($("weathersit").value),
            temp: Number($("temp").value),
            atemp: Number($("atemp").value),
            hum: Number($("hum").value),
            windspeed: Number($("windspeed").value)
        };

        console.log("Sending:", payload);

        try {

            const response = await fetch("/predict", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify(payload)
            });

            const data = await response.json();

            console.log("Prediction:", data);

            if (!response.ok) {
                throw new Error(data.error || "Prediction failed");
            }

            $("demand").textContent =
                Number(data.predicted_demand).toLocaleString();

            $("heroDemand").textContent =
                Number(data.predicted_demand).toLocaleString();

            $("profile").textContent =
                data.demand_profile;

            $("cluster").textContent =
                data.cluster_number;

            $("recommendation").textContent =
                data.recommendation;

            $("resultPanel").scrollIntoView({
                behavior: "smooth",
                block: "center"
            });

        } catch (err) {

            console.error(err);

            error.textContent =
                "Prediction Error: " + err.message;

        } finally {

            button.disabled = false;

            button.innerHTML =
                "<span>⚡</span> Predict Bicycle Demand";
        }
    });


    // -----------------------------
    // ANALYTICS
    // -----------------------------
    async function loadAnalytics() {

        try {

            const response =
                await fetch("/api/analytics");

            const data =
                await response.json();

            console.log("Analytics:", data);

            if (!response.ok) {
                throw new Error(
                    data.error || "Analytics failed"
                );
            }

            drawChart(
                "hourChart",
                data.hourly_demand,
                "hr",
                "hour"
            );

            drawChart(
                "monthChart",
                data.monthly_demand,
                "mnth",
                "month"
            );

            drawChart(
                "weekdayChart",
                data.weekday_demand,
                "weekday",
                "weekday"
            );

            drawChart(
                "weatherChart",
                data.weather_demand,
                "weathersit",
                "weather"
            );

        } catch (err) {

            console.error(
                "Analytics Error:",
                err
            );
        }
    }


    // -----------------------------
    // DRAW CHART
    // -----------------------------
    function drawChart(
        canvasId,
        data,
        key,
        type
    ) {

        const canvas = $(canvasId);

        if (!canvas || !data || data.length === 0) {
            console.error(
                "No chart data:",
                canvasId
            );
            return;
        }

        const width =
            Math.max(
                canvas.parentElement.clientWidth - 30,
                300
            );

        const height = 260;

        const dpr =
            window.devicePixelRatio || 1;

        canvas.width =
            width * dpr;

        canvas.height =
            height * dpr;

        canvas.style.width =
            width + "px";

        canvas.style.height =
            height + "px";

        const ctx =
            canvas.getContext("2d");

        ctx.setTransform(
            dpr,
            0,
            0,
            dpr,
            0,
            0
        );

        ctx.clearRect(
            0,
            0,
            width,
            height
        );


        const values =
            data.map(
                item => Number(item.cnt) || 0
            );

        const labels =
            data.map(
                item => item[key]
            );

        const max =
            Math.max(...values, 1);


        const left = 42;
        const right = 10;
        const top = 15;
        const bottom = 45;

        const chartWidth =
            width - left - right;

        const chartHeight =
            height - top - bottom;


        // Grid

        ctx.strokeStyle =
            "rgba(255,255,255,0.10)";

        for (let i = 0; i <= 4; i++) {

            const y =
                top +
                chartHeight -
                (i / 4) * chartHeight;

            ctx.beginPath();

            ctx.moveTo(
                left,
                y
            );

            ctx.lineTo(
                width - right,
                y
            );

            ctx.stroke();
        }


        // Y labels

        ctx.fillStyle =
            "rgba(220,235,235,0.65)";

        ctx.font =
            "10px Arial";

        ctx.textAlign =
            "right";

        for (let i = 0; i <= 4; i++) {

            const y =
                top +
                chartHeight -
                (i / 4) * chartHeight;

            ctx.fillText(
                Math.round(max * i / 4),
                left - 6,
                y + 3
            );
        }


        // Bars

        const spacing =
            chartWidth / values.length;

        const barWidth =
            Math.max(
                4,
                spacing * 0.65
            );


        values.forEach(
            (value, index) => {

                const barHeight =
                    value / max *
                    chartHeight;

                const x =
                    left +
                    index * spacing +
                    (spacing - barWidth) / 2;

                const y =
                    top +
                    chartHeight -
                    barHeight;


                ctx.fillStyle =
                    "#24d6a3";

                ctx.fillRect(
                    x,
                    y,
                    barWidth,
                    barHeight
                );


                // Label

                let label =
                    labels[index];


                if (type === "month") {

                    const months = [
                        "Jan", "Feb", "Mar",
                        "Apr", "May", "Jun",
                        "Jul", "Aug", "Sep",
                        "Oct", "Nov", "Dec"
                    ];

                    label =
                        months[
                            Number(label) - 1
                        ];
                }


                if (type === "weekday") {

                    const days = [
                        "Sun", "Mon", "Tue",
                        "Wed", "Thu", "Fri",
                        "Sat"
                    ];

                    label =
                        days[
                            Number(label)
                        ];
                }


                if (type === "weather") {

                    const weather = [
                        "Clear",
                        "Mist",
                        "Rain",
                        "Heavy"
                    ];

                    label =
                        weather[
                            Number(label) - 1
                        ];
                }


                const step =
                    Math.max(
                        1,
                        Math.ceil(
                            values.length / 12
                        )
                    );


                if (index % step === 0) {

                    ctx.save();

                    ctx.fillStyle =
                        "rgba(220,235,235,0.65)";

                    ctx.font =
                        "10px Arial";

                    ctx.textAlign =
                        "right";

                    ctx.translate(
                        x + barWidth / 2,
                        height - 8
                    );

                    ctx.rotate(
                        -Math.PI / 5
                    );

                    ctx.fillText(
                        label,
                        0,
                        0
                    );

                    ctx.restore();
                }
            }
        );
    }


    // Start analytics
    loadAnalytics();


    // Redraw when window size changes
    window.addEventListener(
        "resize",
        loadAnalytics
    );

});