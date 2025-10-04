print("Hello World!", flush=True)

# Save hello world to file
with open("hello_world_output.txt", "w") as f:
    f.write("Hello World!")

print("Message saved to hello_world_output.txt", flush=True)
