# amiwrong

#### Video Demo: <https://youtu.be/HyZG9E2aGHA>

#### Description:

amiwrong is a dynamic web application where users can create and vote on polls with rich graphs, optional statement of assumption, and optional demographic insights. Quick and easy registration is required to participate, requiring only a username and password. I used Flask, Bootstrap, Javascript, HTML, and CSS to create the app, with extensive usage of Flask routes and jinja templating. All of the data is stored in a fairly involved sql database with several tables, and interacted with via sqlite3 queries.

Each user has a profile page where they may optionally choose to fill in some preset demographic details, which are used to autofill answers appropriately if a given poll requests demographic details from these presets. For example, a user's age.

The poll results are displayed using chart.js, with a fairly complex feature allowing users to filter results by as many demographic selections as they please from the included demographics options, which uses a special Flask route to query the database appropriate and live refresh the data being used in the graph and chart generation, making for a more insightful and interesting experience. Each poll has a unique_id used in the url, inspired by Youtube.

When creating a poll, the user chooses a question, and may optionally specify an assumption about the future outcome of the poll. They can then add options (minimum of 2) for the users to choose from. They can select as many or few demographic questions to include in the poll from both a list of preset demographics, and custom demographic fields.

The homepage and navbar change appropriately depending on whether or not a user is logged in. The non-logged in home page features an animated typing effect made using typed.js which creates a modern feeling, as well as listing some of the apps core features. The logged in homepage, is where the user can see and navigate to all of their previously created polls. If the user has previously voted on a given poll, then the reults template is rendered. Otherwise, the template where a user may vote on a poll is rendered instead.

I think the level of data validation and secuirty measures implemented in the backend to be sufficient considering the non-commercial nature of this app. Flash messages are used when some error occurs with user input, such as an invalid entry. Included in the web app is a basic privacy policy page, as well as terms of service, which are standard in most modern web apps. Flask decorators are used to enforce user login requirements, for example. bcrypt is the python library used for password salting / hashing.
