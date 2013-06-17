package hxsublime;


#if macro
using haxe.macro.ExprTools;
using haxe.macro.TypeTools;

import haxe.macro.Context;
import haxe.macro.Expr;
import haxe.macro.Expr.ExprOf;
import haxe.macro.Type;
import haxe.macro.TypeTools;
import neko.Lib;
using StringTools;
#end

class FindDeclaration 
{

	#if macro
	static function formatPos (pos:Position) 
	{
		var p = Context.getPosInfos( pos );
		var file = p.file.split("\\").join("/");
		return '|||||{ "file": "$file", "min" : ${p.min}, "max" : ${p.max} }|||||';
	}

	static function redirectTrace () 
	{
		
		haxe.Log.trace = function (msg, ?pos:haxe.PosInfos) 
		{
			var f = pos.fileName;
			var p = f.substr(f.lastIndexOf("/")+1) + ":" + pos.lineNumber;
			out(p + ": " + msg);
		}
	}

	static function error (info:String = "impossible") 
	{
		return '|||||{ "error": "${info}" }|||||';
	}

	static function fromIdent (x) 
	{
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

	static function findInInstance (t:Ref<ClassType>, check) 
	{
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
				var new_interf = [];
				for (i in interf) {
					var fields = i.t.get().fields.get().filter( check );
					if (fields.length == 1)  {
						res = fields[0].pos;	
						break;
					}
					for (i in i.t.get().interfaces) {
						new_interf.push(i);
					}
				}
				if (res != null) break;

				interf = new_interf;
				
			}
		}

		return res;
	}

	static function fromField (x, field:String):Position 
	{
		out(field);
		function check (x:ClassField) 
		{
			return if (field.startsWith("get_") || field.startsWith("set_")) 
			{
				x.name == field.substr(4);
			} else {
				x.name == field;
			}
		}

		var pos = try {
			trace("Trying to get the type of expression x");
			trace("this could fail/stop without a thrown exception (Haxe Compiler Bug in Display mode)");
			var t = Context.typeof( x );
			trace("x was successfull typed as: << " + TypeTools.toString(t) + " >>");
			switch (t) 
			{
				case Type.TInst( t , _ ):
					trace("Search in TInst");
					findInInstance(t, check);

					
				case Type.TType( t , _ ):
					trace("Search in TType");
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
					trace("Search in TAnonymous");
					var fields = a.get().fields.filter(check);
					fields[0].pos;
				case _:

					trace("Declaration is not available");
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

	static var out = Lib.println;

	static function checkRegular (e) 
	{
		
		switch (e.expr) 
		{
			case EConst(CIdent(_)):
				trace("Current Expression is an const Ident");
				var p = fromIdent(e);
				if (p != null) {
					out( formatPos(p) );
				}
			case EField(e, field):
				trace("Current Expression is a field access (EField)");
				var p = fromField(e,field);

				if (p != null)
					out( formatPos(p) );
				else out(error());

			// compiler inlined expression
			case ECall({expr:EFunction(_,
				{ expr : { expr : 
					EReturn( 
						{ expr : EFunction(_, { expr : { expr : EReturn(
							x
						)}})}
					)
				}})}, _):
				trace("Current Expression is a compiler inlined Expression (hard to follow)");
				switch (x) 
				{
					case {expr:ECall({ expr : EField(e, field)}, _)}:
						trace("Inlined Expression contains Field Access, try fromField");
						var p = fromField(e,field);
						if (p != null)
							out( formatPos(p) )
						else out(error());
					case _:
						trace("Inlined Expression cannot be resolved");
						trace("Trigger inline error for sublime, the inline workaround can be triggered from there.");
						out(error("inlined"));
						
				}
			case ECall({expr : EField(e,field)}, args) if (args.length == 0):
				trace("Expression is an ECall from an EField, try fromField");
				var p = fromField(e,field);
				if (p != null) out(formatPos(p))
				else out(error());

			case _:
				out(error());
		}
	}

	static function sublimeFindDecl (e:Expr, eIdent:Expr) 
	{
		redirectTrace();

		trace("-------------------");
		trace("Find Declaration of Expr: " + e.toString());



		// this is a special check, eIdent is only passed to this function
		// if a first regular call was not successfull. This could be
		// the case if the expression was inlined by the compiler
		// and couldn't be checked afterwards.
		switch (eIdent.expr) 
		{
			case EConst(CIdent(fieldName)) if (fieldName != "null"):
				trace("Using Inline Workaround for id " + fieldName);
				var p = fromField(e, fieldName);
				if (p != null) 
				{
					out( formatPos(p) );
					return macro null;
				}
				else out(error());
			case _:
		}

		// if e is a type
		switch (Context.typeof(e)) 
		{
			case TType(t, params):
				trace("Expr is a TType");
				out( formatPos(t.get().pos) );
				return macro null;
			case t:

				trace("Type of Expr is << " + TypeTools.toString(t) + " >>");
		}

		// find decl based on the structure of expression e
		checkRegular(e);

		out("-------------------");
		return macro null;
	}


	#end



	macro public static function __sublimeFindDecl (e:ExprOf<Dynamic>, eIdent:Expr = null):Expr 
	{
		return sublimeFindDecl(e, eIdent);
	}

}