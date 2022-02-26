load("@com_google_protobuf//:protobuf.bzl", _py_proto_library="py_proto_library")
load("@pip_deps//:requirements.bzl", "entry_point")

def _PyiOuts(srcs, use_grpc_plugin = False):
    ret = [s[:-len(".proto")] + "_pb2.pyi" for s in srcs]
    if use_grpc_plugin:
        ret += [s[:-len(".proto")] + "_pb2_grpc.pyi" for s in srcs]
    return ret

def _IsNewExternal(ctx):
    # Bazel 0.4.4 and older have genfiles paths that look like:
    #   bazel-out/local-fastbuild/genfiles/external/repo/foo
    # After the exec root rearrangement, they look like:
    #   ../repo/bazel-out/local-fastbuild/genfiles/foo
    return ctx.label.workspace_root.startswith("../")

def _GetPath(ctx, path):
    if ctx.label.workspace_root:
        return ctx.label.workspace_root + "/" + path
    else:
        return path

def _SourceDir(ctx):
    if not ctx.attr.includes:
        return ctx.label.workspace_root
    if not ctx.attr.includes[0]:
        return _GetPath(ctx, ctx.label.package)
    if not ctx.label.package:
        return _GetPath(ctx, ctx.attr.includes[0])
    return _GetPath(ctx, ctx.label.package + "/" + ctx.attr.includes[0])

def _GenDir(ctx):
    if _IsNewExternal(ctx):
        # We are using the fact that Bazel 0.4.4+ provides repository-relative paths
        # for ctx.genfiles_dir.
        return ctx.genfiles_dir.path + (
            "/" + ctx.attr.includes[0] if ctx.attr.includes and ctx.attr.includes[0] else ""
        )

    # This means that we're either in the old version OR the new version in the local repo.
    # Either way, appending the source path to the genfiles dir works.
    return ctx.var["GENDIR"] + "/" + _SourceDir(ctx)

def _proto_gen_pyi_impl(ctx):
    """General implementation for generating protos

    The implementation is copied from
    https://github.com/protocolbuffers/protobuf/blob/4.0.x/protobuf.bzl
    with the following changes ONLY:
    - Removed `gen_cc` and `gen_py` since we'll keep using `py_proto_library` to generate the
      py source files.
    - Changed the `outs` for each `ctx.actions.run` to be the `.pyi` files (instead of `.py` files)
      which is the output of the `mypy-protobuf` plugin.
    """
    srcs = ctx.files.srcs
    deps = depset(direct=ctx.files.srcs)
    source_dir = _SourceDir(ctx)
    gen_dir = _GenDir(ctx).rstrip("/")
    if source_dir:
        has_sources = any([src.is_source for src in srcs])
        has_generated = any([not src.is_source for src in srcs])
        import_flags = []
        if has_sources:
            import_flags += ["-I" + source_dir]
        if has_generated:
            import_flags += ["-I" + gen_dir]
        import_flags = depset(direct=import_flags)
    else:
        import_flags = depset(direct=["-I."])

    for dep in ctx.attr.deps:
        if type(dep.proto.import_flags) == "list":
            import_flags = depset(transitive=[import_flags], direct=dep.proto.import_flags)
        else:
            import_flags = depset(transitive=[import_flags, dep.proto.import_flags])
        if type(dep.proto.deps) == "list":
            deps = depset(transitive=[deps], direct=dep.proto.deps)
        else:
            deps = depset(transitive=[deps, dep.proto.deps])

    for src in srcs:
        args = []

        in_gen_dir = src.root.path == gen_dir
        if in_gen_dir:
            import_flags_real = []
            for f in import_flags.to_list():
                path = f.replace("-I", "")
                import_flags_real.append("-I$(realpath -s %s)" % path)

        outs = _PyiOuts([src.basename])
        use_grpc_plugin = (ctx.attr.plugin_language == "grpc" and ctx.attr.plugin)
        path_tpl = "$(realpath %s)" if in_gen_dir else "%s"

        outs = [ctx.actions.declare_file(out, sibling = src) for out in outs]
        inputs = [src] + deps.to_list()
        tools = [ctx.executable.protoc]
        if ctx.executable.plugin:
            plugin = ctx.executable.plugin
            lang = ctx.attr.plugin_language
            if not lang and plugin.basename.startswith("protoc-gen-"):
                lang = plugin.basename[len("protoc-gen-"):]
            if not lang:
                fail("cannot infer the target language of plugin", "plugin_language")

            outdir = "." if in_gen_dir else gen_dir

            if ctx.attr.plugin_options:
                outdir = ",".join(ctx.attr.plugin_options) + ":" + outdir
            args += [("--plugin=protoc-gen-%s=" + path_tpl) % (lang, plugin.path)]
            args += ["--%s_out=%s" % (lang, outdir)]
            tools.append(plugin)

        if not in_gen_dir:
            ctx.actions.run(
                inputs = inputs,
                tools = tools,
                outputs = outs,
                arguments = args + import_flags.to_list() + [src.path],
                executable = ctx.executable.protoc,
                mnemonic = "ProtoCompile",
                use_default_shell_env = True,
            )
        else:
            for out in outs:
                orig_command = " ".join(
                    ["$(realpath %s)" % ctx.executable.protoc.path] + args +
                    import_flags_real + ["-I.", src.basename],
                )
                command = ";".join([
                    'CMD="%s"' % orig_command,
                    "cd %s" % src.dirname,
                    "${CMD}",
                    "cd -",
                ])
                generated_out = "/".join([gen_dir, out.basename])
                if generated_out != out.path:
                    command += ";mv %s %s" % (generated_out, out.path)
                ctx.actions.run_shell(
                    inputs = inputs,
                    outputs = [out],
                    command = command,
                    mnemonic = "ProtoCompile",
                    tools = tools,
                    use_default_shell_env = True,
                )

    return struct(
        proto = struct(
            srcs = srcs,
            import_flags = import_flags,
            deps = deps,
        ),
    )

proto_gen_pyi = rule(
    attrs = {
        "srcs": attr.label_list(allow_files = True),
        "deps": attr.label_list(providers = ["proto"]),
        "includes": attr.string_list(),
        "protoc": attr.label(
            cfg = "exec",
            executable = True,
            allow_single_file = True,
            mandatory = True,
        ),
        "plugin": attr.label(
            cfg = "exec",
            allow_files = True,
            executable = True,
        ),
        "plugin_language": attr.string(),
        "plugin_options": attr.string_list(),
        "outs": attr.output_list(),
    },
    output_to_genfiles = True,
    implementation = _proto_gen_pyi_impl,
)

def py_proto_library(
        name,
        srcs = [],
        deps = [],
        py_libs = [],
        py_extra_srcs = [],
        include = None,
        default_runtime = Label("@com_google_protobuf//:protobuf_python"),
        protoc = Label("@com_google_protobuf//:protoc"),
        use_grpc_plugin = False,
        **kargs):
    """Bazel rule to create a Python protobuf library from proto source files.
    """
    outs = _PyiOuts(srcs, use_grpc_plugin)

    includes = []
    if include != None:
        includes = [include]

    proto_gen_pyi(
        name = name + "_genproto_mypy",
        srcs = srcs,
        deps = [d + "_genproto" for d in deps],
        includes = includes,
        protoc = protoc,
        outs = outs,
        visibility = ["//visibility:public"],
        plugin = entry_point(
            pkg = "mypy-protobuf",
            script = "protoc-gen-mypy",
        ),
        plugin_language="mypy",
    )

    _py_proto_library(
        name = name,
        srcs = srcs,
        data = [":" + name + "_genproto_mypy"],
        deps = deps,
        py_libs = py_libs,
        py_extra_srcs = py_extra_srcs,
        include = include,
        default_runtime = default_runtime,
        protoc = protoc,
        use_grpc_plugin = use_grpc_plugin,
        **kargs
    )
