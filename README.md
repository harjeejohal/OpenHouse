Name: Harjee Johal

This repo contains the code for my implementation of the API requirements provided to me.

This web app contains two usable endpoints:

*** API DOCUMENTATION ***

The first endpoint is: `https://openhouse-project.appspot.com/read_logs`: This is the endpoint that can be hit in order to retrieve logs from the database. This endpoint accepts POST requests. The following parameters can be passed in as part of the request body:

"conditions" (Required, dict): This parameter is a dictionary that contains the filter conditions that are applied to the database during the data retrieval. This field is required in order to prevent the retrieval of the entirety of the logs collection in one request. This dictionary can contain any combiniation of the following three keys (at least one must be provided, however):

"conditions.type" (string): This is a string used to specify the type of log that is desired. The known types are CLICK, VIEW, and NAVIGATE. 

"conditions.userId" (string): This is a string that represent the ID of the user who's logs you wish to see. 

"conditions.timerange" (list): This is a list of ISO-8601 formatted timestamps. The list must only contain two timestamps, the beginning of the specified range, and the end of the specified range. Furthermore, the beginning of the specified range must be chronologically before the end of the range.


The second endpoint is: `https://openhouse-project.appspot.com/write_logs`: This is the endpoint used to write the logs to the database. This endpoint also accepts POST requests with a request body. The following parameters are accepted as part of the request body of this endpoint:

"idempotency_key": (string): This is a unique_id that a user can send with their request. Upon the completion of the request, this value with be written to the "idempotency" table. Every time a request comes in with an idempotency key, it's checked against this table. If there's an existing record in the table with the same value, then the incoming request is considered to be a duplicate, so the server returns a message indicating such, which saves the server the time of re-doing the same request. It also helps prevent any potentially insidious side-effects of repeating a request.

"logs": (Required, list): This is a list of all of the logs that are to be written to the database. This is the top level object containing all of them. Each element of this array must adhere to a specific format and standard as well. Any parameters of the form "logs.X" are parameters that exist in each element of the `logs` list.

"logs.userId" (Required, string): This is a string representing the ID of the user who's actions are represented in a given log element. 

"logs.sessionId" (Required, string): This is a string representing the ID of the session of the user who's actions are held in a given log element.

"logs.actions" (Required, list): This is a list of all of the different action-types that a user performed within the span of one session. Like the `logs` array, this array also has required fields for its elements.

"logs.actions.type" (Required, string): This is a string representing the type of action performed by the user.

"logs.actions.time" (Required, string): This is an ISO-8601 formatted timestring of when the user performed the action.

"logs.actions.properties" (dict): This is a dictionary containing all of the relevant metadata about the action.

*** END OF API DOCUMENTATION ***

*** FOLLOW-UP QUESTION ***
I think that my decision to use a SQL-esque database was a reasonable choice here. That's because even though a No-SQL database would be able to flexibly store each log as is during a write, it would lose that flexibility during a read. The reason is that some of the condition parameters are applied to nested fields (type and timerange). No-SQL does not have the query capability to apply these conditions without first flattening out the actions array associated with each log. Therefore, the data must experience some form of flattening regardless of whether we opt to use No-SQL or SQL. Furthermore, even though No-SQL databases can be horizontally-scaled easily, this actually causes problems during writes due to the time it takes to propagate the write's data across all of the scaled nodes (consistency). Thus, I believe the best way to scale this solution is via a vertically-scalable SQL database. We can leverage batch writes to quickly write data, and the data in the database will already be flattened out, making it easier to query during reads.

Another thing that I think might improve scalability is to make the process of writing tags asynchronous. The volume of data being sent has the potential to be very large, with a lot of I/O involved during writes. Therefore, I believe that using some sort of queue-based system might be beneficial. Without a queue, the synchronous write requests will become blocking, prevent a resource from fielding other requests. However, with a queue-based system, writes can instead be processed in smaller, less time-consuming batches. I think there's also added value to this in the fact that any write failures can be written to a separate queue, where they can be analyzed to find any issues that may exist in the process of generating the logs in the first place.

Other ways I would make my solution scalable is by setting up a CI/CD pipeline for it. The deployment process should be automated if possible. This makes it easier to make changes more quickly. Furthermore, the power of a CI/CD pipeline is that you can add additional checks in, such as static code analysis and testing coverage quotas, to ensure that the quality of your code doesn't drop as your development speed increases.

Another thing to note is that my implementation allows for the insertion of duplicate data. During the read, I collapse the data that I return, so that the duplicates don't appear during a read. The reason I did this is to leverage the ability to perform bulk database writes. If I had checks for duplicates, an entire batch could potentially fail due to one duplicated piece of data. However, the reality of the matter is that a scalable solution would find a way to perform batch writes without inserting duplicates. This way, I would be able to leverage bulk writing capabilities and also be able to remove the logic that I added to remove duplicates during a read. This would help remove a potential bottleneck while also preserving the integrity of the database.