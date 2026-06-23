##### LLM <--> Function Call Flow

##### \----------------------------

##### Ensure LLM does not do the work itself

&#x09;- control LLM through system prompt



Tell LLM what is available for it to use to "DO" Work:

&#x09;- create a function that does the required work

&#x09;- create json for that function

&#x09;	- method description is critical

&#x09;	- allows LLM to bind the prompt instructions with the function

&#x09;- let LLM know availability of that function by passing the json

&#x09;- repeat the above for all functions



##### Give a prompt asking LLM to "DO" something

&#x09;- e.g., add two numbers

&#x09;- matches your intent with any available tools

&#x09;- grabs the parameters, tool name and ask you back to invoke the function 

&#x09;- our program checks: is this is a message WITH content OR tool call?

&#x09;- if tool call, our program invokes the tool

&#x09;- \*\*\*our program\*\*\*:

&#x09;	- appends the assistant message in the message history

&#x09;	- invokes the functions with those parameters, 

&#x09;	- creates a response message,

&#x09;	- appends the response message to the message history

&#x09;	- send the response back to LLM

&#x09;

#### LLM

&#x09;- gets the response, creates the final message/reply and responds back.



\-----------------------------------------

# The above is known as ReACT Pattern in agentic AI

\-----------------------------------------

### Prompt: (x + y) - z + ab^2  OR





