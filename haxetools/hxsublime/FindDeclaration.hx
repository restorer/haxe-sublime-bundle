package hxsublime;


#if macro
using haxe.macro.ExprTools;
using haxe.macro.TypeTools;

import haxe.macro.Context;
import haxe.macro.Expr;
import haxe.macro.Expr.ExprOf;
import haxe.macro.Type;
import neko.Lib;
#end

class FindDeclaration {


	macro public static function sublime_find_decl (e:ExprOf<Dynamic>, eIdent:Expr = null):Expr {
		var out = Lib.println;

		//out = Sys.stderr().writeString;

		out("-------------------");
		out(e.toString());
		out("hey");

		


		function formatPos (pos:Position) {
			var p = Context.getPosInfos( pos );
			var file = p.file.split("\\").join("/");
			return '|||||{ "file": "$file", "min" : ${p.min}, "max" : ${p.max} }|||||';
		}

		function error (info:String = "impossible") {
			
			return '|||||{ "error": "${info}" }|||||';
		}

		function fromIdent (x) {
			return try {
				var t = Context.typeof( x );

				var pos = switch (t) {
					case Type.TAbstract( t , _ ): t.get().pos;
					case Type.TEnum( t , _ ): t.get().pos;
					case Type.TInst( t , _ ): t.get().pos;
					case Type.TType( t , _ ): t.get().pos;
					case _: null;

				}

				pos;

				
			} catch (e:Dynamic) {
				null;
			}
		}

		function fromField (x, field) {
			var check = function (x) return x.name == field;
			var pos = try {
				
				var t = Context.typeof( x );

				switch (t) {
					case Type.TInst( t , _ ):
						
						var cur = t;

						var res = null;
						var interf1 = [];

						while (true) {
							var fields = cur.get().fields.get().filter( check );
							if (fields.length == 1)  {
								res = fields[0].pos;	
								break;
							}
							var x = cur.get().superClass;
							if (x == null) break;

							cur = x.t;

							for (i in cur.get().interfaces) {

								interf1.push(i);
							}
						}
						if (res == null) {
							var interf = t.get().interfaces.concat(interf1);
							while (interf.length > 0) {
								var new_interf = []
								for (i in interf) {
									var fields = i.t.get().fields.get().filter( check );
									if (fields.length == 1)  {
										res = fields[0].pos;	
										break;
									}
									for (i in i.t.get().interfaces) {
										new_interf.push(i)
									}
								}
								if (res != null) break;



								interf = new_interf
								
							}
						}

						res;

						
					case Type.TType( t , _ ):

						trace("is ttype");
						switch (t.get().type) {
							case Type.TInst( t , _ ):
								var statics = t.get().statics.get().filter( check );
								var fields = t.get().fields.get().filter( check );
								statics[0].pos;
								
								

							case Type.TAnonymous( a ):
								var fields = a.get().fields.filter(check);
								fields[0].pos;

							case _: 
								trace("unsupported");
								null;


						}
					case Type.TAnonymous( a ):
						var fields = a.get().fields.filter(check);
						fields[0].pos;
					case _:
						trace("declaration is not available");
						null;
				}

				// jump to field
				// consider using
				
			}  catch (e:Dynamic) {
				
				// jump to type
				trace("hey5");
				trace("no type");

				var x2 = macro $x.$field;

				fromIdent(x2);

				
			}
			out("hey5");
			return pos;

		}

		
		switch (eIdent.expr) {
			case EConst(CIdent(id)) if (id != "null"):
				out(id);
				var p = fromField(e, id);
				if (p != null)
					out( formatPos(p) )
				else out(error());
			case _:
				out("hey");
				switch (e.expr) {
					case EConst(CIdent(_)):
						var p = fromIdent(e);
						if (p != null) {
							out( formatPos(p) );
						}
					case EField(e, field):
						out("hey3");
						var p = fromField(e,field);

						if (p != null)
							out( formatPos(p) );
						else out(error());
					case ECall({expr:EFunction(_,
						{ expr : { expr : 
							EReturn( 
								{ expr : EFunction(_, { expr : { expr : EReturn(
									x
								)}})}
							)
						}})}, _):
						
						switch (x) {
							case {expr:ECall({ expr : EField(e, field)}, _)}:
								var p = fromField(e,field);
								if (p != null)
									out( formatPos(p) )
								else out(error());
							case _:
								// find expression in currentclass/currentmethod
								// if possible
								out(error("inlined"));
								//trace(e);
								
						}
					case _:
						out(error());
				}
		}
		trace("hey");
		out("-------------------");
		return macro null;
	}

}