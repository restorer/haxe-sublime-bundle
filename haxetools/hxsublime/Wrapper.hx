package hxsublime;
import neko.vm.Thread;


class Wrapper {
    public static function main () {


        var args = Sys.args();

        
        if (args.length == 0) {
            Sys.println("No process specified");
            Sys.exit(1);
        }

        
        var cmd = args.shift();
        var p = new sys.io.Process(cmd, args);


        var err = p.stderr;
        var out = p.stdout;
        var pin = p.stdin;

        
        
        
        
        
        
        
        
        Thread.create(function () {
            while (true) {
                    try {
                        var b = Sys.stdin().readString(1);
                        if (b == "x") {
                            try {
                                
                                p.kill();
                                Sys.exit(0);
                            } catch (e:Dynamic) {
                                Sys.exit(0);
                            }    
                        }

                    } catch (e:Dynamic) {
                        try {
                            p.kill();
                            Sys.exit(0);
                        } catch (e:Dynamic) {
                            Sys.exit(0);
                        }
                    }
            }
        });
        
        
        




        
        
        


        
        

        var t1 = Thread.create(function () {
            var main = Thread.readMessage(true);
            var sysout = Sys.stdout();

            while (true) {
                try {
                    var msg = out.readByte();
                    sysout.writeByte(msg);
                } catch (e:Dynamic) {
                    break;
                }
            }
            main.sendMessage(null);
        });


        var t2 = Thread.create(function () {
            var main = Thread.readMessage(true);
            var errout = Sys.stderr();
            while (true) {
                try {
                    var msg = err.readByte();
                    errout.writeByte(msg);
                    
                } catch (e:Dynamic) {

                    break;
                }
            }
            main.sendMessage(null);

        });

        t2.sendMessage(Thread.current());

        t1.sendMessage(Thread.current());
        

        Thread.readMessage(true);
        Thread.readMessage(true);
            
    }
}
