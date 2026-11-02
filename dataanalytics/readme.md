## ATTEMPT FOR HTML FORMATTING
<nav class="navbar navbar-expand-lg sticky-top" style="background-color: var(--header-green); border-color: black; border-style: solid; border-width: 2px;">
    <div class="container">
        <a href="/">WEBSITENAME</a>
        <div class="navbar-nav ms-auto" style="display: flex; justify-content: right; align-content: center;">
            <a class="nav-link active" href="">Link1</a>
            <a class="nav-link active" href="">Link2</a>
        </div>
    </div>
</nav>

<div style="background-color: var(--header-green); height: 225px; width: 100%;">
    <div class="container pt-4 text-white">
        <h1 style="display: flex; justify-content: center; align-content: center; padding: 20px;">Real Estate Analysis Engine</h1> 
    </div>

<div class="container" style="background-color: aliceblue; padding: 1rem; border-color: black; border-style: solid; border-width: 2px; width: 50%; height: fit-content; margin: 5px; margin-left: 10px;">
    <div class="hero-search mb-5">
        <form class="row g-3" method="get" action="{{ url_for('index') }}">
            <div class="col-md-4">
                <label class="form-label fw-bold">Suburb</label>
                <input type="text" name="suburb" class="form-control" list="suburbs"
                       value="{{ selected_suburb }}" placeholder="Type or select a suburb">
                <datalist id="suburbs">
                    {% for suburb in suburbs %}
                        <option value="{{ suburb }}"></option>
                    {% endfor %}
                </datalist>
            </div>

            <div class="col-md-4">
                <label class="form-label fw-bold">House type</label>
                <input type="text" name="housetype" class="form-control" list="housetypes"
                       value="{{ selected_housetype }}" placeholder="Type or select a house type">
                <datalist id="destination-cities">
                    {% for housetype in housetypes %}
                        <option value="{{ housetype }}"></option>
                    {% endfor %}
                </datalist>
            </div>

            <div class="col-md-3">
                <label class="form-label fw-bold">Date sold</label>
                <input type="date" name="date" class="form-control" value="{{ selected_date }}">
            </div>
            
            <div class="col-md-1 d-flex align-items-end">
                <button type="submit" class="btn btn-orange w-100">Go</button>
            </div>
        </form>
    </div>
</div>