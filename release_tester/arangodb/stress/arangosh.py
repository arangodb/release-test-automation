def arangosh_runner(queue, resq, arangosh, progressive_timeout):
    """operate one arangosh instance"""
    while True:
        try:
            # all tasks are already there. if done:
            job = queue.get(timeout=0.1)
            print("starting my arangosh task! " + str(job["args"]) + str(job["script"]))
            res = arangosh.run_script_monitored(
                [
                    "stress job",
                    arangosh.cfg.test_data_dir.resolve() / job["script"],
                ],
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
        except Exception as ex:
            print("No more work!" + str(ex))
            resq.put(-1)
            break
