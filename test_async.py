import asyncio

# Global list
check_length = True
    
# crawl people
async def task_1():
    a = []
    for i in range(1, 51):
        print('task1:', i)
        a.append({'people': i})
        await asyncio.sleep(0.25)
    return a

# crawl profile
async def task_2(a):
    a['skill'] = 'a'
    print(str(a))

async def auto_call_function(interval, a_many):
    print(a_many)
    await asyncio.sleep(2)
    global check_length
    for a in a_many:
        print(a)
        await task_2(a)
        # if len(a) > 0:
            # Call your function here
        # task2_done = asyncio.create_task(task_2(a))
        # await task2_done
        # elif check_length:
        #     check_length = False
        #     continue
        # else:
        #     print("vô")
        #     break
        # Wait for the specified interval before calling the function again
    await asyncio.sleep(interval)

# talent_sourcing_result_process
async def main():
    interval = 1
    task1_done = asyncio.create_task(task_1())
    a_many = await task1_done
    await auto_call_function(interval, a_many)
    
    # task2_done = asyncio.create_task(task_2())
    # await task2_done

# Run the main coroutine
asyncio.run(main())
