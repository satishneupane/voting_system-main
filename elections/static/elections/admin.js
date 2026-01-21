document.addEventListener("DOMContentLoaded", function() {
    const provinceSelect = document.getElementById("id_province");
    const districtSelect = document.getElementById("id_district");

    if (!provinceSelect || !districtSelect) return;

        provinceSelect.addEventListener("change", function() {
            const provinceId = this.value;

            // Fetch districts via AJAX
            fetch(`/ajax/districts-by-province/?province_id=${provinceId}`)
                .then(response => response.json())
                .then(data => {
                    districtSelect.innerHTML = '';
                    data.forEach(district => {
                        const option = document.createElement("option");
                        option.value = d.id;
                        option.text = d.name;
                        districtSelect.appendChild(option);
                    });
                });
        });
    }
);