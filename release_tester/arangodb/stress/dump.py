def dump_runner(queue, resq, dump, progressive_timeout):
    """operate one arangosh instance"""
    while True:
        try:
            # all tasks are already there. if done:
            job = queue.get(timeout=0.1)
            print(job)
            print("starting my dump task! " + str(job["args"]) + str(job["dir"]))
            res = dump.run_dump_monitored(
                basepath=str(dump.cfg.base_test_dir.resolve() / job["dir"]),
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
        except Empty as ex:
            print("No more work!" + str(ex))
            resq.put(-1)
            break
        except Exception as ex:
            print("".join(traceback.TracebackException.from_exception(ex).format()))
            break
