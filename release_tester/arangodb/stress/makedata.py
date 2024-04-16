def makedata_runner(queue, resq, arangosh, one_shard, progressive_timeout):
    """operate one makedata instance"""
    while True:
        try:
            # all tasks are already there. if done:
            job = queue.get(timeout=0.1)
            print("starting my task! " + str(job["args"]))
            res = arangosh.create_test_data(
                "xx",
                one_shard,
                "_system",
                args=job["args"],
                result_line_handler=result_line,
                progressive_timeout=progressive_timeout,
            )
            if not res[0]:
                print("error executing test - giving up.")
                print(res[1])
                resq.put(1)
                break
            resq.put(res)
        # pylint: disable=broad-except
        except Exception as ex:
            print("No more work!" + str(ex))
            resq.put(-1)
            break
